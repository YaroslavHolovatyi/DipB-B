"""Smoke tests for the auth flow."""

from __future__ import annotations

import secrets

import httpx


async def test_signup_login_refresh_me(client: httpx.AsyncClient) -> None:
    suffix = secrets.token_hex(4)
    creds = {
        "first_name": "Alice",
        "username": f"alice_{suffix}",
        "email": f"alice_{suffix}@taverntest.com",
        "password": "topsecret123",
        "main_city_id": 1,
    }

    # Signup
    response = await client.post("/auth/signup", json=creds)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["username"] == creds["username"]
    tokens = body["tokens"]
    assert tokens["access_token"] and tokens["refresh_token"]

    # /auth/me with the access token
    me = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == creds["email"].lower()

    # Login with username
    login = await client.post(
        "/auth/login",
        json={"identifier": creds["username"], "password": creds["password"]},
    )
    assert login.status_code == 200

    # Refresh
    refresh = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 200
    new_tokens = refresh.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


async def test_login_with_wrong_password_is_401(client: httpx.AsyncClient) -> None:
    suffix = secrets.token_hex(4)
    creds = {
        "first_name": "Bob",
        "username": f"bob_{suffix}",
        "email": f"bob_{suffix}@taverntest.com",
        "password": "rightpassword",
        "main_city_id": 1,
    }
    await client.post("/auth/signup", json=creds)
    bad = await client.post(
        "/auth/login",
        json={"identifier": creds["email"], "password": "wrongpassword"},
    )
    assert bad.status_code == 401


async def test_me_without_token_is_401(client: httpx.AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401
