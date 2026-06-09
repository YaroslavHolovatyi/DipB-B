"""
Receipt OCR adapter.

Wraps the call to OpenAI's Vision model. In local dev (no API key) the stub
returns a deterministic mock parse so the split-room flow can be exercised
end-to-end without spending tokens.

The shape we return — `ParsedReceipt` — mirrors the columns of `check_items`
plus a couple of header fields. The route handler that creates a check uses
this directly to populate the row + line items.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Domain types
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class ParsedItem:
    name: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal


@dataclass(slots=True)
class ParsedReceipt:
    bar_name: str | None
    currency: str
    total_amount: Decimal
    items: list[ParsedItem]
    # Raw provider response, stored verbatim in checks.ocr_payload for audit.
    raw: dict[str, Any]


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #
class OcrService(Protocol):
    async def parse_receipt(self, image_url: str) -> ParsedReceipt: ...


# --------------------------------------------------------------------------- #
# Stub — returns a fixed, plausible Lviv beer-bar receipt
# --------------------------------------------------------------------------- #
class StubOcrService:
    """Deterministic mock — does NOT call OpenAI. Used when OPENAI_API_KEY is empty."""

    async def parse_receipt(self, image_url: str) -> ParsedReceipt:  # noqa: ARG002
        logger.info("StubOcrService: returning mock parse")
        items = [
            ParsedItem(name="Львівське світле 0.5л", quantity=Decimal("4"),
                       unit_price=Decimal("65.00"), total_price=Decimal("260.00")),
            ParsedItem(name="Картопля по-селянськи", quantity=Decimal("2"),
                       unit_price=Decimal("130.00"), total_price=Decimal("260.00")),
            ParsedItem(name="Сирне асорті",            quantity=Decimal("1"),
                       unit_price=Decimal("220.00"), total_price=Decimal("220.00")),
            ParsedItem(name="Цезар з куркою",          quantity=Decimal("1"),
                       unit_price=Decimal("180.00"), total_price=Decimal("180.00")),
        ]
        total = sum((it.total_price for it in items), Decimal("0"))
        raw = {
            "provider": "stub",
            "items": [
                {"name": i.name, "qty": float(i.quantity),
                 "unit": float(i.unit_price), "total": float(i.total_price)}
                for i in items
            ],
            "total": float(total),
        }
        return ParsedReceipt(
            bar_name="Кумпель",
            currency="UAH",
            total_amount=total,
            items=items,
            raw=raw,
        )


# --------------------------------------------------------------------------- #
# Live — OpenAI Vision (kept lazy so dev installs don't need the openai SDK)
# --------------------------------------------------------------------------- #
class OpenAiOcrService:
    """Live implementation against OpenAI Vision. Requires `OPENAI_API_KEY`."""

    _PROMPT = (
        "Extract the line items from this receipt photo. Reply ONLY with JSON "
        "matching: {currency:'UAH', bar_name:str|null, items:[{name, qty, unit_price, total_price}], "
        "total:number}. Use floats. No commentary."
    )

    def __init__(self, api_key: str, model: str) -> None:
        # `openai` SDK is imported lazily so the test suite doesn't require it.
        from openai import AsyncOpenAI  # noqa: PLC0415

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def parse_receipt(self, image_url: str) -> ParsedReceipt:
        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._PROMPT},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )
        raw_text = completion.choices[0].message.content or "{}"
        raw: dict[str, Any] = json.loads(raw_text)
        items = [
            ParsedItem(
                name=str(i["name"]),
                quantity=Decimal(str(i.get("qty", 1))),
                unit_price=Decimal(str(i.get("unit_price", 0))),
                total_price=Decimal(str(i.get("total_price", 0))),
            )
            for i in raw.get("items", [])
        ]
        return ParsedReceipt(
            bar_name=raw.get("bar_name"),
            currency=str(raw.get("currency", "UAH")),
            total_amount=Decimal(str(raw.get("total", sum((i.total_price for i in items), Decimal("0"))))),
            items=items,
            raw=raw,
        )


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def build_ocr_service() -> OcrService:
    """Pick the live or stub implementation based on settings."""
    if settings.openai_api_key:
        return OpenAiOcrService(settings.openai_api_key, settings.openai_model_vision)
    return StubOcrService()
