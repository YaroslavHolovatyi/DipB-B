"""
Health endpoints.

Three flavours, all under `/health`:

    GET /health        — liveness, always returns 200. No I/O.
    GET /health/db     — runs `SELECT 1` through SQLAlchemy. 503 on failure.
    GET /health/redis  — `PING` against Redis.            503 on failure.

These are used by `scripts/verify-setup.sh`, by Docker healthchecks once we
deploy, and by humans to debug local setup.
"""

from __future__ import annotations

from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.redis import get_redis

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: Literal["ok"] = "ok"


class DependencyStatus(BaseModel):
    status: Literal["ok", "error"]
    detail: str | None = None


@router.get("", response_model=HealthStatus)
async def liveness() -> HealthStatus:
    """Always returns OK. Used by load balancers for liveness."""
    return HealthStatus()


@router.get("/db", response_model=DependencyStatus)
async def db_readiness(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> DependencyStatus:
    """Verify the DB is reachable by running `SELECT 1`."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"db unreachable: {exc!s}",
        ) from exc
    return DependencyStatus(status="ok")


@router.get("/redis", response_model=DependencyStatus)
async def redis_readiness(
    r: Annotated[aioredis.Redis, Depends(get_redis)],
) -> DependencyStatus:
    """Verify Redis is reachable with PING."""
    try:
        pong = await r.ping()
        if not pong:
            raise RuntimeError("PING returned falsy")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"redis unreachable: {exc!s}",
        ) from exc
    return DependencyStatus(status="ok")
