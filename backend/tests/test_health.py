"""Smoke tests for the /health endpoints."""

from __future__ import annotations

import httpx


async def test_liveness(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_db_readiness(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_redis_readiness(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/redis")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
