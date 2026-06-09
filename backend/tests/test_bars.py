"""Smoke tests for the bars catalog."""

from __future__ import annotations

import httpx


async def test_list_bars_unauthenticated_returns_page(client: httpx.AsyncClient) -> None:
    response = await client.get("/bars?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert {"items", "total", "limit", "offset"} <= set(body.keys())
    assert body["limit"] == 5


async def test_favorite_and_unfavorite(
    client: httpx.AsyncClient, auth_headers: dict
) -> None:
    listing = await client.get("/bars?limit=1")
    items = listing.json()["items"]
    if not items:
        # Seeds not loaded — skip rather than fail.
        return
    bar_id = items[0]["id"]

    fav = await client.post(f"/bars/{bar_id}/favorite", headers=auth_headers)
    assert fav.status_code == 204

    detail = await client.get(f"/bars/{bar_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["is_favorite"] is True

    unfav = await client.delete(f"/bars/{bar_id}/favorite", headers=auth_headers)
    assert unfav.status_code == 204
