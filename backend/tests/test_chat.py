"""Smoke test for sending one chat message between two users."""

from __future__ import annotations

import secrets

import httpx


async def test_send_direct_message(client: httpx.AsyncClient) -> None:
    # Create two users
    users = []
    for who in ("alice", "bob"):
        suffix = secrets.token_hex(4)
        body = {
            "first_name": who,
            "username": f"{who}_{suffix}",
            "email": f"{who}_{suffix}@taverntest.com",
            "password": "supersecret123",
            "main_city_id": 1,
        }
        response = await client.post("/auth/signup", json=body)
        assert response.status_code == 201
        users.append(response.json())

    alice, bob = users
    a_headers = {"Authorization": f"Bearer {alice['tokens']['access_token']}"}

    # Alice opens a direct conversation with Bob
    convo = await client.post(
        "/chat/conversations",
        json={"type": "direct", "participant_ids": [bob["user"]["id"]]},
        headers=a_headers,
    )
    assert convo.status_code == 201, convo.text
    convo_id = convo.json()["id"]

    # Alice sends a message
    msg = await client.post(
        f"/chat/conversations/{convo_id}/messages",
        json={"body": "Drink at Кумпель at 8?"},
        headers=a_headers,
    )
    assert msg.status_code == 201
    assert msg.json()["body"] == "Drink at Кумпель at 8?"
