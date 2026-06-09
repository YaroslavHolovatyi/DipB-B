"""
Event → Check linkage tests (WP5).

After a raid finishes, the host can photograph the single shared bill and open
a split room pre-seeded with everyone who showed up. These tests prove:

  * POST /checks/from-event links the check to the raid and seeds the verified
    attendees as `invited` participants (host as `joined`);
  * a second bill for the same event is rejected;
  * only the host may split the bill.

The OCR step uses the deterministic StubOcrService when no OPENAI_API_KEY is
set, so assertions stay structural (items present, positive total) rather than
pinned to a specific receipt.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import httpx

IMAGE_URL = "https://example.test/receipts/shared-bill.jpg"


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


async def _raid_with_verified_member(
    client: httpx.AsyncClient, host_h: dict, member: dict, member_h: dict
) -> dict:
    when = (datetime.now(tz=timezone.utc) + timedelta(hours=3)).isoformat()
    raid = (
        await client.post(
            "/raids",
            json={"title": "Crawl then split", "scheduled_at": when},
            headers=host_h,
        )
    ).json()
    await client.post(f"/raids/{raid['id']}/rsvp", json={"status": "going"}, headers=member_h)
    await client.post(
        f"/raids/{raid['id']}/verify",
        json={"marks": [{"user_id": member["user"]["id"], "verdict": "attended"}]},
        headers=host_h,
    )
    return raid


async def test_from_event_seeds_attendees(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _raid_with_verified_member(client, h, member, m)

    res = await client.post(
        "/checks/from-event",
        json={"image_url": IMAGE_URL, "raid_id": raid["id"]},
        headers=h,
    )
    assert res.status_code == 201, res.text
    check = res.json()

    assert check["raid_id"] == raid["id"]
    assert check["party_id"] is None
    assert len(check["items"]) > 0
    assert float(check["total_amount"]) > 0

    # Host owns the room (joined); the verified attendee is invited to pick items.
    by_user = {p.get("user_id"): p for p in check["participants"]}
    assert by_user[host["user"]["id"]]["status"] == "joined"
    assert by_user[member["user"]["id"]]["status"] == "invited"


async def test_duplicate_bill_rejected(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _raid_with_verified_member(client, h, member, m)
    body = {"image_url": IMAGE_URL, "raid_id": raid["id"]}

    first = await client.post("/checks/from-event", json=body, headers=h)
    assert first.status_code == 201, first.text

    second = await client.post("/checks/from-event", json=body, headers=h)
    assert second.status_code == 409, second.text


async def test_only_host_can_split(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    member = await _signup(client, "member")
    h, m = _headers(host), _headers(member)

    raid = await _raid_with_verified_member(client, h, member, m)

    res = await client.post(
        "/checks/from-event",
        json={"image_url": IMAGE_URL, "raid_id": raid["id"]},
        headers=m,  # the attendee, not the host
    )
    assert res.status_code == 403, res.text


async def test_requires_exactly_one_event(client: httpx.AsyncClient) -> None:
    host = await _signup(client, "host")
    h = _headers(host)

    # Neither raid_id nor party_id → 400.
    res = await client.post(
        "/checks/from-event", json={"image_url": IMAGE_URL}, headers=h
    )
    assert res.status_code == 400, res.text
