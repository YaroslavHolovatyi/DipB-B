"""
LLM adapter for the Tavern Tales (AI Dungeon Master) feature.

Provides `chat_completion(messages)` and `stream_completion(messages)` so the
session router can either return the full reply (simple) or stream it as
Server-Sent Events (smoother UX). The stub returns a canned response that
still demonstrates the message-role + metadata flow.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LlmReply:
    content: str
    tokens_in: int
    tokens_out: int
    metadata: dict[str, Any]   # parsed JSON state_change / request_roll, if any


class LlmService(Protocol):
    async def chat_completion(self, messages: list[dict[str, str]]) -> LlmReply: ...

    def stream_completion(
        self, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]: ...


# --------------------------------------------------------------------------- #
# Stub
# --------------------------------------------------------------------------- #
_STUB_REPLY = (
    "The tavern keeper looks up as you approach. \"Aye, traveler — what brings "
    "you to the Drunken Dragon tonight?\" He polishes a mug and waits."
)


class StubLlmService:
    async def chat_completion(self, messages: list[dict[str, str]]) -> LlmReply:  # noqa: ARG002
        logger.info("StubLlmService: returning canned reply")
        return LlmReply(content=_STUB_REPLY, tokens_in=50, tokens_out=40, metadata={})

    async def stream_completion(  # type: ignore[override]
        self, messages: list[dict[str, str]]  # noqa: ARG002
    ) -> AsyncIterator[str]:
        # Emit a few chunks so the client sees streaming behaviour.
        for chunk in _STUB_REPLY.split(". "):
            yield chunk + (". " if not chunk.endswith(".") else "")


# --------------------------------------------------------------------------- #
# Live — OpenAI chat
# --------------------------------------------------------------------------- #
class OpenAiLlmService:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI  # noqa: PLC0415

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def chat_completion(self, messages: list[dict[str, str]]) -> LlmReply:
        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        choice = completion.choices[0]
        usage = completion.usage
        return LlmReply(
            content=choice.message.content or "",
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            metadata={},
        )

    async def stream_completion(  # type: ignore[override]
        self, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            stream=True,
        )
        async for event in stream:
            delta = event.choices[0].delta.content if event.choices else None
            if delta:
                yield delta


def build_llm_service() -> LlmService:
    if settings.openai_api_key:
        return OpenAiLlmService(settings.openai_api_key, settings.openai_model_chat)
    return StubLlmService()
