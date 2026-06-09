"""
Expo Push notification adapter.

Each device registers an `ExponentPushToken[...]` via `POST /users/me/push-tokens`.
When something happens that needs to reach the user (raid invite, friend
request, kind-soul awarded, etc.), the notifications service calls
`push.send(...)`. The stub just logs the payload so we can verify the flow
locally without hitting Expo's servers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

EXPO_PUSH_API = "https://exp.host/--/api/v2/push/send"


@dataclass(slots=True)
class PushMessage:
    to: list[str]                      # ExponentPushToken[...] strings
    title: str
    body: str
    data: dict[str, Any]               # deep-link payload picked up by the app
    sound: str = "default"


class PushService(Protocol):
    async def send(self, message: PushMessage) -> None: ...


class StubPushService:
    """Logs only — never hits the network."""

    async def send(self, message: PushMessage) -> None:
        logger.info(
            "StubPushService: would push to %d device(s): %r / %r",
            len(message.to), message.title, message.body,
        )


class ExpoPushService:
    """Live Expo Push client. Single batched POST."""

    async def send(self, message: PushMessage) -> None:
        if not message.to:
            return
        payload = [
            {
                "to": tok,
                "title": message.title,
                "body": message.body,
                "data": message.data,
                "sound": message.sound,
            }
            for tok in message.to
        ]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(EXPO_PUSH_API, json=payload)
        if response.is_error:
            logger.warning("expo push failed: %s %s", response.status_code, response.text)


def build_push_service() -> PushService:
    # We don't have a meaningful "is configured?" signal for Expo (no key needed),
    # so the toggle is just the env flag: if app_env is local AND we're in debug,
    # stub it. Otherwise call Expo for real.
    if settings.app_env == "local" and settings.app_debug:
        return StubPushService()
    return ExpoPushService()
