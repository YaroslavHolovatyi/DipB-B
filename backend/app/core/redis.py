"""
Shared Redis client.

A single async `redis.asyncio.Redis` instance is created at app startup
(via the FastAPI lifespan) and reused for the lifetime of the process. The
client is used for:

    - Pub/Sub fan-out between Uvicorn workers (realtime layer).
    - Short-TTL caching of hot queries (added per-feature as needed).

We expose a thin module-level holder so tests can swap the client out, and
`get_redis()` as a FastAPI dependency for use in endpoints.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings


class _RedisState:
    """Mutable holder so we can attach/detach the client at lifespan boundaries."""

    client: aioredis.Redis | None = None


_state = _RedisState()


async def connect_redis() -> aioredis.Redis:
    """Create the shared Redis client. Call once from the FastAPI lifespan."""
    if _state.client is None:
        _state.client = aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
        )
    return _state.client


async def disconnect_redis() -> None:
    """Close the shared client. Call once from the FastAPI lifespan."""
    if _state.client is not None:
        await _state.client.aclose()
        _state.client = None


def get_redis() -> aioredis.Redis:
    """
    Return the shared Redis client.

    Used as a FastAPI dependency:

        @router.get("/...")
        async def handler(r: Redis = Depends(get_redis)):
            ...
    """
    if _state.client is None:
        raise RuntimeError(
            "Redis client is not initialised. Did the FastAPI lifespan run?"
        )
    return _state.client
