"""
Parties integration tests — create + join + roster.

A party is the lighter-weight "hang out" object (no attendance verification).
Here we just prove the host can open one and a second user can join, with the
member roster reflecting both and the host's own membership intact.
"""

from __future__ import annotations

import secrets

import httpx


async def _signup(client: httpx.AsyncClient, who: str) -> dict:
    suffix = secrets.token_hex(4)
    body = {
        "first_name": who,
        "username": f"{who}_{suffix}",
        "email": f"{who}_{suffix}@taverntest.com",
        "password": "supersecret123",
        "main_city_id": 1,
    }
    response = await client.post("/auth/signup", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _headers(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['tokens']['access_token']}"}


async def test_create_and_join_party(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    guest = await _signup(client, "guest")
    h, g = _headers(host), _headers(guest)

    created = await client.post(
        "/parties",
        json={"title": "Patio pints", "max_members": 6},
        headers=h,
    )
    assert created.status_code == 201, created.text
    party = created.json()
    assert party["host_id"] == host["user"]["id"]
    assert party["status"] == "open"
    # The host is counted as a member from the start.
    assert party["member_count"] == 1
    assert party["my_membership"] == "joined"

    joined = await client.post(f"/parties/{party['id']}/join", headers=g)
    assert joined.status_code == 200, joined.text
    assert joined.json()["my_membership"] == "joined"
    assert joined.json()["member_count"] == 2

    members = await client.get(f"/parties/{party['id']}/members", headers=h)
    assert members.status_code == 200, members.text
    ids = {row["user_id"] for row in members.json()}
    assert host["user"]["id"] in ids
    assert guest["user"]["id"] in ids


async def test_leave_party_drops_member_count(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    guest = await _signup(client, "guest")
    h, g = _headers(host), _headers(guest)

    party = (
        await client.post("/parties", json={"title": "Quiz night"}, headers=h)
    ).json()

    await client.post(f"/parties/{party['id']}/join", headers=g)
    left = await client.post(f"/parties/{party['id']}/leave", headers=g)
    assert left.status_code == 200, left.text
    assert left.json()["my_membership"] == "left"
    assert left.json()["member_count"] == 1


async def test_host_cancels_party(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    h = _headers(host)

    party = (
        await client.post("/parties", json={"title": "Maybe later"}, headers=h)
    ).json()
    cancelled = await client.patch(
        f"/parties/{party['id']}", json={"status": "cancelled"}, headers=h
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
