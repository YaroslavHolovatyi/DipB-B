"""
Receipt OCR service — OpenAI Vision adapter.
=============================================

Supersedes the root-level prototype (`receipt_processing_workflow.py`).
Integrates cleanly with the project's service registry pattern.

Two concrete implementations are provided:

``ReceiptOcrService``
    Live implementation.  Encodes the image (URL *or* raw bytes) and sends it
    to GPT-4o Vision via the Chat Completions API with ``response_format =
    json_object``.  Retries up to ``max_retries`` times on transient network
    errors before re-raising.

``StubReceiptOcrService``
    Deterministic mock used when ``OPENAI_API_KEY`` is absent.  Returns a
    realistic Lviv bar receipt so the split-room flow works end-to-end without
    spending tokens.

Both classes satisfy ``OcrService`` from ``app.services.ocr`` so the registry
can swap them in without touching any caller.

Public helpers
--------------
``build_receipt_ocr_service()``
    Factory — returns the live or stub implementation based on
    ``settings.openai_api_key``.

``encode_image_bytes(data, mime_type)``
    Turns raw bytes into an OpenAI-compatible ``image_url`` data-URI so any
    caller (e.g. the checks router handling a direct file upload) can reuse the
    same path as a remote URL.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Literal

from app.core.config import settings
from app.services.ocr import ParsedItem, ParsedReceipt  # shared domain types

logger = logging.getLogger(__name__)

# Supported MIME types accepted both by us and by the OpenAI Vision API.
SupportedMime = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]

_ALLOWED_MIMES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/gif", "image/webp"}
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def encode_image_bytes(data: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Build an OpenAI-compatible ``data:`` URI from raw bytes.

    Use this when the caller has the image in memory (e.g. a file upload)
    rather than a publicly reachable URL.

    Args:
        data:      Raw image bytes.
        mime_type: MIME type — must be one of the four types supported by the
                   OpenAI Vision API (jpeg / png / gif / webp).

    Returns:
        A ``data:<mime_type>;base64,<encoded>`` string that can be passed
        directly to ``parse_receipt_url`` or used as the ``url`` field in an
        OpenAI image_url content block.

    Raises:
        ValueError: If ``mime_type`` is not one of the supported types.
    """
    if mime_type not in _ALLOWED_MIMES:
        raise ValueError(
            f"Unsupported mime type '{mime_type}'. "
            f"Must be one of: {sorted(_ALLOWED_MIMES)}"
        )
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def mime_from_path(path: str | Path) -> str:
    """Guess the MIME type from a file extension; falls back to image/jpeg."""
    guessed, _ = guess_type(str(path))
    if guessed in _ALLOWED_MIMES:
        return guessed
    return "image/jpeg"


# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #

_SYSTEM_PROMPT = (
    "You are a precise receipt-parsing assistant. "
    "Always respond with a single JSON object — no markdown fences, no commentary."
)

_USER_PROMPT = (
    "Extract every line item from this receipt photo and return ONLY valid JSON "
    "that matches this exact schema:\n\n"
    "{\n"
    '  "bar_name": "<merchant name or null>",\n'
    '  "currency": "<3-letter ISO code, default UAH>",\n'
    '  "items": [\n'
    '    {"name": "<item name>", "qty": <float>, "unit_price": <float>, "total_price": <float>}\n'
    "  ],\n"
    '  "subtotal": <float>,\n'
    '  "tax_amount": <float or 0>,\n'
    '  "total": <float>,\n'
    '  "confidence": <0.0..1.0>  // your estimate of parse quality\n'
    "}\n\n"
    "Rules:\n"
    "- All monetary values must be floats.\n"
    "- `total` should equal `subtotal` + `tax_amount`; if the image is unclear use the printed total.\n"
    "- `qty` defaults to 1 if not explicitly shown.\n"
    "- `confidence` reflects how clearly the receipt text was readable (1.0 = perfect).\n"
    "- If you cannot read the receipt at all, return an empty `items` list and `confidence: 0`.\n"
    "- Never invent items that are not on the receipt."
)


# --------------------------------------------------------------------------- #
# Parse helpers
# --------------------------------------------------------------------------- #

def _safe_decimal(value: Any, fallback: Decimal = Decimal("0")) -> Decimal:
    """Convert a JSON value to Decimal without throwing."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return fallback


def _parse_raw(raw: dict[str, Any]) -> ParsedReceipt:
    """
    Turn the JSON dict returned by the Vision model into a ``ParsedReceipt``.

    Handles minor inconsistencies in the model output (missing keys, wrong
    types) so the caller always gets a typed result.
    """
    items: list[ParsedItem] = []
    for idx, item in enumerate(raw.get("items") or []):
        try:
            name = str(item.get("name") or f"Item {idx + 1}").strip()
            qty = _safe_decimal(item.get("qty", 1), Decimal("1"))
            unit_price = _safe_decimal(item.get("unit_price", 0))
            total_price = _safe_decimal(
                item.get("total_price") or item.get("total", 0)
            )
            # Derive total if missing / inconsistent.
            if total_price == Decimal("0") and unit_price > 0:
                total_price = (unit_price * qty).quantize(Decimal("0.01"))
            items.append(ParsedItem(
                name=name,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price,
            ))
        except Exception:
            logger.warning("Skipping malformed item at index %d: %r", idx, item)

    # Fall back to summing items if the model didn't provide a top-level total.
    computed_total = sum((i.total_price for i in items), Decimal("0"))
    total_amount = _safe_decimal(raw.get("total"), computed_total)
    currency = str(raw.get("currency") or "UAH").upper()[:3]

    return ParsedReceipt(
        bar_name=raw.get("bar_name") or None,
        currency=currency,
        total_amount=total_amount,
        items=items,
        raw=raw,
    )


# --------------------------------------------------------------------------- #
# Live implementation
# --------------------------------------------------------------------------- #

class ReceiptOcrService:
    """
    OpenAI GPT-4o Vision receipt parser.

    Supports two input modes:

    * **URL** — publicly reachable image URL (e.g. an S3 pre-signed URL).
    * **Bytes** — raw file upload encoded via :func:`encode_image_bytes`.

    The underlying ``parse_receipt`` method (URL only) satisfies the
    ``OcrService`` protocol from ``app.services.ocr``, making this class a
    drop-in replacement for ``OpenAiOcrService``.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 1024,
        max_retries: int = 2,
    ) -> None:
        # Deferred import — avoids forcing the openai SDK on the test suite.
        from openai import AsyncOpenAI  # noqa: PLC0415

        self._client = AsyncOpenAI(api_key=api_key, max_retries=max_retries)
        self._model = model
        self._max_tokens = max_tokens

    # ---------------------------------------------------------------------- #
    # Protocol surface
    # ---------------------------------------------------------------------- #

    async def parse_receipt(self, image_url: str) -> ParsedReceipt:
        """
        Parse a receipt reachable at ``image_url``.

        ``image_url`` may be:
        * A regular ``https://`` URL.
        * A ``data:image/...;base64,...`` URI produced by :func:`encode_image_bytes`.

        This is the method required by the ``OcrService`` protocol.
        """
        return await self._call_vision(image_url)

    # ---------------------------------------------------------------------- #
    # Extended surface
    # ---------------------------------------------------------------------- #

    async def parse_receipt_bytes(
        self,
        data: bytes,
        mime_type: str = "image/jpeg",
    ) -> ParsedReceipt:
        """
        Parse a receipt from raw bytes (e.g. a direct file upload).

        Encodes the image as a data-URI and delegates to :meth:`parse_receipt`.

        Args:
            data:      Raw image bytes — e.g. ``await upload_file.read()``.
            mime_type: MIME type string.  Must be jpeg / png / gif / webp.

        Returns:
            :class:`~app.services.ocr.ParsedReceipt` with all extracted fields.
        """
        data_uri = encode_image_bytes(data, mime_type)
        return await self._call_vision(data_uri)

    async def parse_receipt_path(self, path: str | Path) -> ParsedReceipt:
        """
        Convenience: read a local file and parse it.

        Primarily useful in tests and scripts.  In production, prefer
        :meth:`parse_receipt_bytes` after reading the upload.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Receipt image not found: {path}")
        mime = mime_from_path(path)
        data = path.read_bytes()
        return await self.parse_receipt_bytes(data, mime)

    # ---------------------------------------------------------------------- #
    # Internal
    # ---------------------------------------------------------------------- #

    async def _call_vision(self, image_url: str) -> ParsedReceipt:
        """Send the image to the Vision API and parse the JSON response."""
        logger.debug("Calling OpenAI Vision (%s) for receipt parse", self._model)

        completion = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _USER_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                # "auto" lets OpenAI choose detail level;
                                # "high" gives more tokens for dense receipts.
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
        )

        raw_text: str = completion.choices[0].message.content or "{}"
        logger.debug(
            "Vision response (%d chars, finish=%s): %.200s",
            len(raw_text),
            completion.choices[0].finish_reason,
            raw_text,
        )

        try:
            raw: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("OpenAI Vision returned invalid JSON: %s", raw_text[:500])
            raise ValueError(
                f"OpenAI Vision returned non-JSON content: {exc}"
            ) from exc

        result = _parse_raw(raw)

        confidence: float = float(raw.get("confidence", 1.0))
        if confidence < 0.4:
            logger.warning(
                "Low OCR confidence (%.2f) for receipt — items may be incomplete",
                confidence,
            )

        logger.info(
            "Receipt parsed: %d items, total=%s %s, confidence=%.2f",
            len(result.items),
            result.total_amount,
            result.currency,
            confidence,
        )
        return result


# --------------------------------------------------------------------------- #
# Stub — no API key required
# --------------------------------------------------------------------------- #

class StubReceiptOcrService:
    """
    Deterministic mock.  Does NOT call OpenAI.

    Used automatically when ``OPENAI_API_KEY`` is not set so the full
    split-room flow can be exercised in local dev without spending tokens.
    """

    async def parse_receipt(self, image_url: str) -> ParsedReceipt:  # noqa: ARG002
        logger.info("StubReceiptOcrService: returning deterministic mock parse")
        return self._mock_receipt()

    async def parse_receipt_bytes(
        self, data: bytes, mime_type: str = "image/jpeg"  # noqa: ARG002
    ) -> ParsedReceipt:
        logger.info("StubReceiptOcrService.parse_receipt_bytes: returning mock")
        return self._mock_receipt()

    async def parse_receipt_path(self, path: str | Path) -> ParsedReceipt:  # noqa: ARG002
        logger.info("StubReceiptOcrService.parse_receipt_path: returning mock")
        return self._mock_receipt()

    @staticmethod
    def _mock_receipt() -> ParsedReceipt:
        items = [
            ParsedItem(
                name="Львівське світле 0.5л",
                quantity=Decimal("4"),
                unit_price=Decimal("65.00"),
                total_price=Decimal("260.00"),
            ),
            ParsedItem(
                name="Картопля по-селянськи",
                quantity=Decimal("2"),
                unit_price=Decimal("130.00"),
                total_price=Decimal("260.00"),
            ),
            ParsedItem(
                name="Сирне асорті",
                quantity=Decimal("1"),
                unit_price=Decimal("220.00"),
                total_price=Decimal("220.00"),
            ),
            ParsedItem(
                name="Цезар з куркою",
                quantity=Decimal("1"),
                unit_price=Decimal("180.00"),
                total_price=Decimal("180.00"),
            ),
        ]
        total = sum((it.total_price for it in items), Decimal("0"))
        raw: dict[str, Any] = {
            "provider": "stub",
            "bar_name": "Кумпель",
            "currency": "UAH",
            "items": [
                {
                    "name": i.name,
                    "qty": float(i.quantity),
                    "unit_price": float(i.unit_price),
                    "total_price": float(i.total_price),
                }
                for i in items
            ],
            "subtotal": float(total),
            "tax_amount": 0.0,
            "total": float(total),
            "confidence": 1.0,
        }
        return ParsedReceipt(
            bar_name="Кумпель",
            currency="UAH",
            total_amount=total,
            items=items,
            raw=raw,
        )


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

def build_receipt_ocr_service() -> ReceiptOcrService | StubReceiptOcrService:
    """
    Pick the live or stub implementation based on application settings.

    Returns ``ReceiptOcrService`` when ``OPENAI_API_KEY`` is set in the
    environment / ``.env`` file; otherwise ``StubReceiptOcrService``.

    Intended to be called once at application start from the service registry::

        from app.services.receipt_ocr_service import build_receipt_ocr_service
        _ocr = build_receipt_ocr_service()
    """
    if settings.openai_api_key:
        logger.info(
            "ReceiptOcrService: live mode (model=%s)", settings.openai_model_vision
        )
        return ReceiptOcrService(
            api_key=settings.openai_api_key,
            model=settings.openai_model_vision,
        )

    logger.warning(
        "OPENAI_API_KEY not set — using StubReceiptOcrService (mock data only)"
    )
    return StubReceiptOcrService()
