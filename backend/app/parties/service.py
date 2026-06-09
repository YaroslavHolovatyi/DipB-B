"""
Parties service.

A Party is interest-matched, venue-optional, and lightweight. Discovery sorts
by how many of a party's interests overlap the viewer's own interests (the
`match_score`), so people see the most relevant parties first — nothing is
hidden. Creating or joining requires a completed profile (bio + ≥1 interest),
which is what makes the matching meaningful.
"""

from __future__ import annotations

from datetime import UTC, datetime

import redis.asyncio as aioredis
from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.friends.models import UserFriend
from app.notifications import service as notifications_service
from app.parties.models import Party, PartyDrink, PartyInterest, PartyMember
from app.parties.schemas import (
    PartyCreate,
    PartyListParams,
    PartyMemberRead,
    PartyRead,
    PartyUpdate,
)
from app.reference.models import Drink, RaceDrink
from app.services.push import PushService
from app.shared.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.users.models import Interest, UserInterest


# --------------------------------------------------------------------------- #
# Gates & shared expressions
# --------------------------------------------------------------------------- #
async def _require_profile(db: AsyncSession, user_id: int) -> None:
    """Parties only work if people have a bio + interests to match on."""
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("user not found")
    interest_count = (
        await db.execute(
            select(func.count(UserInterest.interest_id)).where(
                UserInterest.user_id == user_id
            )
        )
    ).scalar_one()
    if not (user.bio and user.bio.strip()) or int(interest_count) == 0:
        raise BadRequestError(
            "add a bio and at least one interest to your profile first"
        )


def _member_count_expr():
    return (
        select(func.count(PartyMember.user_id))
        .where(
            PartyMember.party_id == Party.id,
            PartyMember.status == "joined",
        )
        .correlate(Party)
        .scalar_subquery()
    )


def _match_score_expr(viewer_id: int):
    """How many of this party's interests the viewer also has."""
    return (
        select(func.count(PartyInterest.interest_id))
        .join(
            UserInterest,
            UserInterest.interest_id == PartyInterest.interest_id,
        )
        .where(
            PartyInterest.party_id == Party.id,
            UserInterest.user_id == viewer_id,
        )
        .correlate(Party)
        .scalar_subquery()
    )


def _viewer_drink_types(viewer_id: int):
    """The drink types implied by the viewer's quiz-assigned race."""
    return (
        select(Drink.type)
        .join(RaceDrink, RaceDrink.drink_id == Drink.id)
        .join(User, User.race_id == RaceDrink.race_id)
        .where(User.id == viewer_id)
    )


def _drink_match_expr(viewer_id: int):
    """How many of this party's drink tags match the viewer's race taste."""
    return (
        select(func.count(PartyDrink.drink_type))
        .where(
            PartyDrink.party_id == Party.id,
            PartyDrink.drink_type.in_(_viewer_drink_types(viewer_id)),
        )
        .correlate(Party)
        .scalar_subquery()
    )


def _my_membership_expr(viewer_id: int):
    return (
        select(PartyMember.status)
        .where(
            PartyMember.party_id == Party.id,
            PartyMember.user_id == viewer_id,
        )
        .correlate(Party)
        .scalar_subquery()
    )


def _visibility_filter(viewer_id: int):
    """Visible when open, hosted by, joined by, or a friend of the host."""
    is_member = exists().where(
        PartyMember.party_id == Party.id,
        PartyMember.user_id == viewer_id,
        PartyMember.status == "joined",
    )
    is_friend = exists().where(
        UserFriend.user_id == Party.host_id,
        UserFriend.friend_id == viewer_id,
        UserFriend.status == "accepted",
    )
    return or_(
        Party.visibility == "open",
        Party.host_id == viewer_id,
        is_member,
        is_friend,
    )


async def _interest_ids_for(db: AsyncSession, party_ids: list[int]) -> dict[int, list[int]]:
    if not party_ids:
        return {}
    rows = (
        await db.execute(
            select(PartyInterest.party_id, PartyInterest.interest_id)
            .where(PartyInterest.party_id.in_(party_ids))
            .order_by(PartyInterest.interest_id.asc())
        )
    ).all()
    out: dict[int, list[int]] = {pid: [] for pid in party_ids}
    for pid, iid in rows:
        out.setdefault(pid, []).append(iid)
    return out


async def _drink_types_for(db: AsyncSession, party_ids: list[int]) -> dict[int, list[str]]:
    if not party_ids:
        return {}
    rows = (
        await db.execute(
            select(PartyDrink.party_id, PartyDrink.drink_type)
            .where(PartyDrink.party_id.in_(party_ids))
            .order_by(PartyDrink.drink_type.asc())
        )
    ).all()
    out: dict[int, list[str]] = {pid: [] for pid in party_ids}
    for pid, dt in rows:
        out.setdefault(pid, []).append(dt)
    return out


def _to_read(
    party: Party,
    *,
    member_count: int,
    match_score: int,
    my_membership: str | None,
    interest_ids: list[int],
    drink_types: list[str],
    drink_match: int,
) -> PartyRead:
    is_full = party.max_members is not None and member_count >= party.max_members
    return PartyRead(
        id=party.id,
        host_id=party.host_id,
        title=party.title,
        description=party.description,
        max_members=party.max_members,
        visibility=party.visibility,
        status=party.status,
        interest_ids=interest_ids,
        drink_types=drink_types,
        member_count=int(member_count or 0),
        match_score=int(match_score or 0),
        drink_match=int(drink_match or 0),
        my_membership=my_membership,
        is_full=bool(is_full),
        created_at=party.created_at,
    )


# --------------------------------------------------------------------------- #
# Listing
# --------------------------------------------------------------------------- #
async def list_parties(
    db: AsyncSession, viewer_id: int, params: PartyListParams
) -> tuple[list[PartyRead], int]:
    mc = _member_count_expr()
    ms = _match_score_expr(viewer_id)
    dm = _drink_match_expr(viewer_id)
    mm = _my_membership_expr(viewer_id)

    stmt = select(Party, mc.label("mc"), ms.label("ms"), dm.label("dm"), mm.label("mm"))
    count_stmt = select(func.count(Party.id))

    vis = _visibility_filter(viewer_id)
    stmt = stmt.where(vis)
    count_stmt = count_stmt.where(vis)

    if params.scope == "mine":
        mine = or_(
            Party.host_id == viewer_id,
            exists().where(
                PartyMember.party_id == Party.id,
                PartyMember.user_id == viewer_id,
                PartyMember.status == "joined",
            ),
        )
        stmt = stmt.where(mine)
        count_stmt = count_stmt.where(mine)

    if params.status is not None:
        stmt = stmt.where(Party.status == params.status)
        count_stmt = count_stmt.where(Party.status == params.status)

    # Best interest match first, then taste (drink) match, then freshest.
    stmt = stmt.order_by(ms.desc(), dm.desc(), Party.created_at.desc())
    stmt = stmt.limit(params.limit).offset(params.offset)

    rows = (await db.execute(stmt)).all()
    total = (await db.execute(count_stmt)).scalar_one()

    parties = [r[0] for r in rows]
    party_ids = [p.id for p in parties]
    interests = await _interest_ids_for(db, party_ids)
    drinks = await _drink_types_for(db, party_ids)

    items = [
        _to_read(
            r[0],
            member_count=r.mc,
            match_score=r.ms,
            my_membership=r.mm,
            interest_ids=interests.get(r[0].id, []),
            drink_types=drinks.get(r[0].id, []),
            drink_match=r.dm,
        )
        for r in rows
    ]
    return items, int(total)


async def get_party(db: AsyncSession, viewer_id: int, party_id: int) -> PartyRead:
    mc = _member_count_expr()
    ms = _match_score_expr(viewer_id)
    dm = _drink_match_expr(viewer_id)
    mm = _my_membership_expr(viewer_id)
    row = (
        await db.execute(
            select(Party, mc.label("mc"), ms.label("ms"), dm.label("dm"), mm.label("mm"))
            .where(Party.id == party_id, _visibility_filter(viewer_id))
        )
    ).first()
    if row is None:
        raise NotFoundError("party not found")
    interests = await _interest_ids_for(db, [party_id])
    drinks = await _drink_types_for(db, [party_id])
    return _to_read(
        row[0],
        member_count=row.mc,
        match_score=row.ms,
        my_membership=row.mm,
        interest_ids=interests.get(party_id, []),
        drink_types=drinks.get(party_id, []),
        drink_match=row.dm,
    )


async def list_members(
    db: AsyncSession, viewer_id: int, party_id: int
) -> list[PartyMemberRead]:
    await get_party(db, viewer_id, party_id)  # visibility / existence
    rows = (
        await db.execute(
            select(
                PartyMember.user_id,
                User.username,
                User.first_name,
                User.avatar_url,
                PartyMember.status,
                PartyMember.joined_at,
            )
            .join(User, User.id == PartyMember.user_id)
            .where(
                PartyMember.party_id == party_id,
                PartyMember.status != "left",
            )
            .order_by(PartyMember.joined_at.asc())
        )
    ).all()
    return [
        PartyMemberRead(
            user_id=uid,
            username=username,
            first_name=first_name,
            avatar_url=avatar_url,
            status=status,
            joined_at=joined_at,
        )
        for (uid, username, first_name, avatar_url, status, joined_at) in rows
    ]


# --------------------------------------------------------------------------- #
# Create / update
# --------------------------------------------------------------------------- #
async def _validate_interest_ids(db: AsyncSession, interest_ids: list[int]) -> list[int]:
    cleaned = sorted(set(interest_ids))
    if not cleaned:
        return []
    found = (
        await db.execute(
            select(Interest.id).where(Interest.id.in_(cleaned))
        )
    ).scalars().all()
    missing = set(cleaned) - set(found)
    if missing:
        raise BadRequestError(f"unknown interest ids: {sorted(missing)}")
    return cleaned


async def create_party(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    *,
    host_id: int,
    payload: PartyCreate,
) -> PartyRead:
    await _require_profile(db, host_id)
    interest_ids = await _validate_interest_ids(db, payload.interest_ids)

    party = Party(
        host_id=host_id,
        title=payload.title,
        description=payload.description,
        max_members=payload.max_members,
        visibility=payload.visibility,
    )
    db.add(party)
    await db.flush()

    db.add(PartyMember(party_id=party.id, user_id=host_id, status="joined"))
    for iid in interest_ids:
        db.add(PartyInterest(party_id=party.id, interest_id=iid))
    for dt in sorted(set(payload.drink_types)):
        db.add(PartyDrink(party_id=party.id, drink_type=dt))

    await db.commit()

    for uid in payload.invite_user_ids:
        if uid == host_id:
            continue
        await _notify_invite(db, redis, push, party, host_id, uid)

    return await get_party(db, host_id, party.id)


async def update_party(
    db: AsyncSession, actor_id: int, party_id: int, payload: PartyUpdate
) -> PartyRead:
    party = await db.get(Party, party_id)
    if party is None:
        raise NotFoundError("party not found")
    if party.host_id != actor_id:
        raise ForbiddenError("only the host can update a party")

    data = payload.model_dump(exclude_unset=True)
    interest_ids = data.pop("interest_ids", None)
    drink_types = data.pop("drink_types", None)
    for k, v in data.items():
        setattr(party, k, v)

    if interest_ids is not None:
        cleaned = await _validate_interest_ids(db, interest_ids)
        await db.execute(
            delete(PartyInterest).where(PartyInterest.party_id == party_id)
        )
        for iid in cleaned:
            db.add(PartyInterest(party_id=party_id, interest_id=iid))

    if drink_types is not None:
        await db.execute(
            delete(PartyDrink).where(PartyDrink.party_id == party_id)
        )
        for dt in sorted(set(drink_types)):
            db.add(PartyDrink(party_id=party_id, drink_type=dt))

    await db.commit()
    return await get_party(db, actor_id, party_id)


# --------------------------------------------------------------------------- #
# Join / leave / invite
# --------------------------------------------------------------------------- #
async def join_party(db: AsyncSession, user_id: int, party_id: int) -> PartyRead:
    party = await db.get(Party, party_id)
    if party is None:
        raise NotFoundError("party not found")
    if party.status == "cancelled":
        raise ConflictError("party is cancelled")
    if party.status != "open":
        raise ConflictError("party is not open to join")

    existing = await db.get(PartyMember, (party_id, user_id))
    if existing is not None and existing.status == "joined":
        return await get_party(db, user_id, party_id)

    await _require_profile(db, user_id)

    if party.max_members is not None:
        joined = (
            await db.execute(
                select(func.count(PartyMember.user_id)).where(
                    PartyMember.party_id == party_id,
                    PartyMember.status == "joined",
                    PartyMember.user_id != user_id,
                )
            )
        ).scalar_one()
        if int(joined) >= party.max_members:
            raise ConflictError("party is already full")

    if existing is None:
        db.add(PartyMember(party_id=party_id, user_id=user_id, status="joined"))
    else:
        existing.status = "joined"
    await db.commit()
    return await get_party(db, user_id, party_id)


async def leave_party(db: AsyncSession, user_id: int, party_id: int) -> PartyRead:
    party = await db.get(Party, party_id)
    if party is None:
        raise NotFoundError("party not found")
    if party.host_id == user_id:
        raise BadRequestError("the host can't leave; cancel the party instead")

    member = await db.get(PartyMember, (party_id, user_id))
    if member is not None and member.status != "left":
        member.status = "left"
        await db.commit()
    return await get_party(db, user_id, party_id)


async def invite_to_party(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    actor_id: int,
    party_id: int,
    user_ids: list[int],
) -> PartyRead:
    party = await db.get(Party, party_id)
    if party is None:
        raise NotFoundError("party not found")
    if party.host_id != actor_id:
        raise ForbiddenError("only the host can invite to a party")

    for uid in set(user_ids):
        if uid == actor_id:
            continue
        member = await db.get(PartyMember, (party_id, uid))
        if member is None:
            db.add(PartyMember(party_id=party_id, user_id=uid, status="invited"))
        elif member.status == "left":
            member.status = "invited"
    await db.commit()

    for uid in set(user_ids):
        if uid == actor_id:
            continue
        await _notify_invite(db, redis, push, party, actor_id, uid)

    return await get_party(db, actor_id, party_id)


async def _notify_invite(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    party: Party,
    sender_id: int,
    recipient_id: int,
) -> None:
    try:
        await notifications_service.create_and_deliver(
            db, redis, push,
            recipient_id=recipient_id,
            sender_id=sender_id,
            type="party_invite",
            title="You're invited to a party",
            body=party.title,
            data={"party_id": party.id},
            related_entity_type="party",
            related_entity_id=party.id,
        )
    except Exception:  # noqa: BLE001 — best-effort per recipient
        return


__all__ = [
    "list_parties", "get_party", "list_members",
    "create_party", "update_party",
    "join_party", "leave_party", "invite_to_party",
    "datetime", "UTC",
]
