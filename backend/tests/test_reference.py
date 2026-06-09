"""Smoke tests for the reference-data endpoints."""

from __future__ import annotations

import httpx


async def test_list_cities(client: httpx.AsyncClient) -> None:
    response = await client.get("/reference/cities")
    assert response.status_code == 200
    body = response.json()
    # The baseline schema seeds Lviv via `database/seeds/01_lviv_bars.sql`.
    assert any(c["slug"] == "lviv" for c in body)


async def test_list_vibes_returns_list(client: httpx.AsyncClient) -> None:
    response = await client.get("/reference/vibes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_races_returns_list(client: httpx.AsyncClient) -> None:
    response = await client.get("/reference/races")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
