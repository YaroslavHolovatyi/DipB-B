"""
Redis Pub/Sub bridge.

Multiple Uvicorn workers can be subscribed to the same Redis channel; when
worker A publishes a message, every worker (including A) receives it on
their `PubSub` instance. The bridge translates those Redis frames into
calls on the local `ConnectionManager`, which then writes to whichever
sockets happen to live on that worker.

Channel conventions
-------------------
- `user:{user_id}`   — events targeted at a specific user (push-style).
- `conv:{conv_id}`   — events shared by every participant in a conversation.
- `check:{check_id}` — events for everyone in a split-room session.

The bridge only knows about `user:*` channels for now; conversation / check
channels will be subscribed to dynamically as those features come online.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.realtime.manager import manager

logger = logging.getLogger(__name__)

USER_CHANNEL_PREFIX = "user:"


def user_channel(user_id: int) -> str:
    """Canonical name for a per-user channel."""
    return f"{USER_CHANNEL_PREFIX}{user_id}"


async def publish_user(redis: aioredis.Redis, user_id: int, event: dict[str, Any]) -> None:
    """Publish an event onto the user-scoped channel."""
    await redis.publish(user_channel(user_id), json.dumps(event))


# --------------------------------------------------------------------------- #
# Long-running listener
# --------------------------------------------------------------------------- #
class PubSubBridge:
    """
    Owns a background task that subscribes to `user:*` and forwards inbound
    messages to the local `ConnectionManager`. Start/stop via lifespan.
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis
        self._task: asyncio.Task[None] | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stopping.clear()
        self._task = asyncio.create_task(self._run(), name="pubsub-bridge")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stopping.set()
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    # ----------------------------------------------------------------- #
    # Internals
    # ----------------------------------------------------------------- #
    async def _run(self) -> None:
        pubsub = self._redis.pubsub()
        # psubscribe so we can pattern-match every user channel from one socket.
        await pubsub.psubscribe(f"{USER_CHANNEL_PREFIX}*")
        logger.info("pubsub bridge subscribed to %s*", USER_CHANNEL_PREFIX)

        try:
            async for raw in pubsub.listen():
                if self._stopping.is_set():
                    break
                if raw is None or raw.get("type") != "pmessage":
                    continue
                await self._handle(raw)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("pubsub bridge crashed")
        finally:
            await pubsub.punsubscribe(f"{USER_CHANNEL_PREFIX}*")
            await pubsub.aclose()

    async def _handle(self, frame: dict[str, Any]) -> None:
        channel: str = frame["channel"]
        if not channel.startswith(USER_CHANNEL_PREFIX):
            return
        try:
            user_id = int(channel[len(USER_CHANNEL_PREFIX):])
        except ValueError:
            logger.warning("dropping pubsub frame with bad channel %r", channel)
            return
        try:
            payload = json.loads(frame["data"])
        except (TypeError, json.JSONDecodeError):
            logger.warning("dropping non-JSON pubsub frame on %s", channel)
            return
        await manager.broadcast_user(user_id, payload)


# Module-level holder so we can start/stop from the FastAPI lifespan.
_bridge: PubSubBridge | None = None


async def start_pubsub(redis: aioredis.Redis) -> None:
    global _bridge
    if _bridge is None:
        _bridge = PubSubBridge(redis)
    await _bridge.start()


async def stop_pubsub() -> None:
    global _bridge
    if _bridge is not None:
        await _bridge.stop()
        _bridge = None
