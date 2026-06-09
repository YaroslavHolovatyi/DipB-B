"""
Raid lifecycle + rating engine integration tests.

Exercises the full host/participant flow against the live app:

    create raid → participant RSVPs → host verifies / completes

and asserts the social-rating side effects land on the participant's
`/users/me/stats` payload (attended credits, no-shows penalise, reliability
is derived). These are the WP6/WP7 "rating engine stays honest" guarantees.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

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


async def _my_stats(client: httpx.AsyncClient, headers: dict[str, str]) -> dict:
    res = await client.get("/users/me/stats", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


async def _create_raid(client: httpx.AsyncClient, headers: dict[str, str]) -> dict:
    when = (datetime.now(tz=timezone.utc) + timedelta(hours=3)).isoformat()
    res = await client.post(
        "/raids",
        json={"title": "Friday beer crawl", "scheduled_at": when},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


async def test_no_show_drops_rating(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _create_raid(client, h)
    member_id = member["user"]["id"]

    # Member commits, then the host marks them a no-show at verification.
    rsvp = await client.post(f"/raids/{raid['id']}/rsvp", json={"status": "going"}, headers=m)
    assert rsvp.status_code == 200, rsvp.text

    before = await _my_stats(client, m)

    verify = await client.post(
        f"/raids/{raid['id']}/verify",
        json={"marks": [{"user_id": member_id, "verdict": "no_show"}]},
        headers=h,
    )
    assert verify.status_code == 200, verify.text

    after = await _my_stats(client, m)
    assert after["events_ditched"] == before["events_ditched"] + 1
    assert after["social_rating"] == before["social_rating"] - 25
    assert after["events_total"] == before["events_total"] + 1


async def test_attended_credits_rating(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _create_raid(client, h)
    member_id = member["user"]["id"]

    await client.post(f"/raids/{raid['id']}/rsvp", json={"status": "going"}, headers=m)
    before = await _my_stats(client, m)

    verify = await client.post(
        f"/raids/{raid['id']}/verify",
        json={"marks": [{"user_id": member_id, "verdict": "attended"}]},
        headers=h,
    )
    assert verify.status_code == 200, verify.text

    after = await _my_stats(client, m)
    assert after["events_attended"] == before["events_attended"] + 1
    assert after["social_rating"] == before["social_rating"] + 1
    # Only attended events so far → perfect reliability.
    if after["events_ditched"] == 0:
        assert after["reliability_pct"] == 100


async def test_complete_marks_unverified_as_no_show(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _create_raid(client, h)

    await client.post(f"/raids/{raid['id']}/rsvp", json={"status": "going"}, headers=m)
    before = await _my_stats(client, m)

    # Host never verifies the member, then wraps the raid up.
    done = await client.post(f"/raids/{raid['id']}/complete", headers=h)
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "completed"

    after = await _my_stats(client, m)
    assert after["events_ditched"] == before["events_ditched"] + 1
    assert after["social_rating"] == before["social_rating"] - 25


async def test_verify_is_idempotent(client: httpx.AsyncClient) -> None:
    """A second verify pass for an already-scored participant is a no-op."""
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _create_raid(client, h)
    member_id = member["user"]["id"]
    await client.post(f"/raids/{raid['id']}/rsvp", json={"status": "going"}, headers=m)

    marks = {"marks": [{"user_id": member_id, "verdict": "no_show"}]}
    await client.post(f"/raids/{raid['id']}/verify", json=marks, headers=h)
    once = await _my_stats(client, m)

    await client.post(f"/raids/{raid['id']}/verify", json=marks, headers=h)
    twice = await _my_stats(client, m)

    assert twice["social_rating"] == once["social_rating"]
    assert twice["events_ditched"] == once["events_ditched"]
