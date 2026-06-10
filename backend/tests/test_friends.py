"""Friends: user search + request lifecycle reflected in search results."""

from __future__ import annotations

import secrets

import httpx


async def _signup(client: httpx.AsyncClient, who: str) -> dict:
    suffix = secrets.token_hex(4)
    body = {
        "first_name": who.capitalize(),
        "username": f"{who}_{suffix}",
        "email": f"{who}_{suffix}@taverntest.com",
        "password": "supersecret123",
        "main_city_id": 1,
    }
    response = await client.post("/auth/signup", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _auth(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['tokens']['access_token']}"}


async def test_search_users_and_friendship_flow(client: httpx.AsyncClient) -> None:
    alice = await _signup(client, "alice")
    bob = await _signup(client, "bob")
    bob_username = bob["user"]["username"]

    # Alice finds Bob by (partial, case-insensitive) username
    res = await client.get(
        "/friends/search",
        params={"q": bob_username[:10].upper()},
        headers=_auth(alice),
    )
    assert res.status_code == 200, res.text
    hits = {r["user"]["id"]: r for r in res.json()}
    assert bob["user"]["id"] in hits
    assert hits[bob["user"]["id"]]["relationship"] == "none"

    # Alice never finds herself
    assert alice["user"]["id"] not in hits

    # Alice sends a friend request -> outgoing for Alice, incoming for Bob
    req = await client.post(
        "/friends/requests",
        json={"recipient_id": bob["user"]["id"]},
        headers=_auth(alice),
    )
    assert req.status_code == 201, req.text
    request_id = req.json()["id"]

    res = await client.get(
        "/friends/search", params={"q": bob_username}, headers=_auth(alice)
    )
    hit = res.json()[0]
    assert hit["relationship"] == "outgoing"
    assert hit["request_id"] == request_id

    res = await client.get(
        "/friends/search",
        params={"q": alice["user"]["username"]},
        headers=_auth(bob),
    )
    hit = res.json()[0]
    assert hit["relationship"] == "incoming"
    assert hit["request_id"] == request_id

    # Bob accepts -> both see each other as friends
    accept = await client.post(
        f"/friends/requests/{request_id}/accept", headers=_auth(bob)
    )
    assert accept.status_code == 200, accept.text

    res = await client.get(
        "/friends/search", params={"q": bob_username}, headers=_auth(alice)
    )
    assert res.json()[0]["relationship"] == "friend"

    friends = await client.get("/friends", headers=_auth(alice))
    assert any(f["user"]["id"] == bob["user"]["id"] for f in friends.json())


async def test_search_rejects_short_query(client: httpx.AsyncClient) -> None:
    user = await _signup(client, "carol")
    res = await client.get("/friends/search", params={"q": "x"}, headers=_auth(user))
    assert res.status_code == 422
