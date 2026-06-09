"""
Raids service.

Highlights:

* On create, the organiser is auto-RSVP'd as `going`. An invitation produces
  a `raid_invite` notification (+ Expo Push if offline).
* On accept (RSVP `going`/`maybe`), the user is added to the auto-created
  raid conversation (chat). On `declined`, they leave it.
* Geo: `?near_lat/near_lon/radius_m` uses PostGIS ST_DWithin against either
  the raid's explicit `location` or the linked bar's location.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis
from geoalchemy2 import Geometry
from sqlalchemy import Float, and_, asc, case, delete, desc, exists, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.bars.models import Bar
from app.friends.models import UserFriend
from app.notifications import service as notifications_service
from app.raids.models import Raid, RaidDrink, RaidParticipant
from app.reference.models import Drink, RaceDrink
from app.raids.schemas import (
    RaidCreate,
    RaidListParams,
    RaidParticipantDetail,
    RaidRead,
    RaidUpdate,
    RaidVerify,
)


# Rating tuning constants (WP6). Verified attendance nudges the score up by a
# small amount; a no-show is penalised harshly so reliability is hard-won and
# easily lost. Clamped to the DB CHECK range [0, 1000].
RATING_FLOOR = 0
RATING_CEILING = 1000
RATING_ATTENDED_DELTA = 1
RATING_NO_SHOW_DELTA = -25

# When a raid has no explicit ends_at, assume it runs this long for the
# purpose of detecting double-booking.
DEFAULT_RAID_DURATION = timedelta(hours=2)


def _window(scheduled_at: datetime, ends_at: datetime | None) -> tuple[datetime, datetime]:
    return scheduled_at, ends_at or (scheduled_at + DEFAULT_RAID_DURATION)


def _clamp_rating(value: int) -> int:
    return max(RATING_FLOOR, min(RATING_CEILING, value))


def _visibility_filter(viewer_id: int):
    """A raid is visible to a viewer when it's open, they organise it, they
    already RSVP'd, or they're an accepted friend of the organiser."""
    is_participant = exists().where(
        RaidParticipant.raid_id == Raid.id,
        RaidParticipant.user_id == viewer_id,
    )
    is_friend = exists().where(
        UserFriend.user_id == Raid.organizer_id,
        UserFriend.friend_id == viewer_id,
        UserFriend.status == "accepted",
    )
    return or_(
        Raid.visibility == "open",
        Raid.organizer_id == viewer_id,
        is_participant,
        is_friend,
    )
from app.services.push import PushService
from app.shared.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _raid_location_expr():
    """Expression that gives a non-null geography for a raid:
    its own `location` if set, otherwise the linked bar's `location`."""
    return func.coalesce(Raid.location, Bar.location)


def _viewer_drink_types(viewer_id: int):
    """The drink types implied by the viewer's quiz-assigned race."""
    return (
        select(Drink.type)
        .join(RaceDrink, RaceDrink.drink_id == Drink.id)
        .join(User, User.race_id == RaceDrink.race_id)
        .where(User.id == viewer_id)
    )


def _drink_match_expr(viewer_id: int):
    """How many of this raid's drink tags match the viewer's race taste."""
    return (
        select(func.count(RaidDrink.drink_type))
        .where(
            RaidDrink.raid_id == Raid.id,
            RaidDrink.drink_type.in_(_viewer_drink_types(viewer_id)),
        )
        .correlate(Raid)
        .scalar_subquery()
    )


async def _drink_types_for(db: AsyncSession, raid_ids: list[int]) -> dict[int, list[str]]:
    if not raid_ids:
        return {}
    rows = (
        await db.execute(
            select(RaidDrink.raid_id, RaidDrink.drink_type)
            .where(RaidDrink.raid_id.in_(raid_ids))
            .order_by(RaidDrink.drink_type.asc())
        )
    ).all()
    out: dict[int, list[str]] = {rid: [] for rid in raid_ids}
    for rid, dt in rows:
        out.setdefault(rid, []).append(dt)
    return out


def _row_to_read(row, *, viewer_id: int, drink_types: list[str] | None = None) -> RaidRead:
    (
        raid_id, title, description, bar_id, organizer_id, scheduled_at, ends_at,
        max_participants, theme, status, visibility, cover_image_url,
        latitude, longitude, distance_m, participant_count, my_rsvp, drink_match,
    ) = row
    return RaidRead(
        id=raid_id,
        title=title,
        description=description,
        bar_id=bar_id,
        organizer_id=organizer_id,
        scheduled_at=scheduled_at,
        ends_at=ends_at,
        max_participants=max_participants,
        theme=theme,
        status=status,
        visibility=visibility,
        cover_image_url=cover_image_url,
        latitude=latitude,
        longitude=longitude,
        distance_m=distance_m,
        participant_count=int(participant_count or 0),
        drink_types=drink_types or [],
        drink_match=int(drink_match or 0),
        my_rsvp=my_rsvp,
    )


def _raid_columns(*, viewer_id: int, near_lat: float | None, near_lon: float | None):
    """Common SELECT for raid listing/detail."""
    loc = _raid_location_expr()
    distance = (
        func.ST_Distance(
            loc,
            func.ST_SetSRID(func.ST_MakePoint(near_lon, near_lat), 4326),
        )
        if near_lat is not None and near_lon is not None
        else literal(None)
    )

    participant_count = (
        select(func.count(RaidParticipant.user_id))
        .where(
            RaidParticipant.raid_id == Raid.id,
            RaidParticipant.status.in_(("going", "maybe")),
        )
        .correlate(Raid)
        .scalar_subquery()
    )

    my_rsvp = (
        select(RaidParticipant.status)
        .where(
            RaidParticipant.raid_id == Raid.id,
            RaidParticipant.user_id == viewer_id,
        )
        .correlate(Raid)
        .scalar_subquery()
    )

    return (
        Raid.id,
        Raid.title,
        Raid.description,
        Raid.bar_id,
        Raid.organizer_id,
        Raid.scheduled_at,
        Raid.ends_at,
        Raid.max_participants,
        Raid.theme,
        Raid.status,
        Raid.visibility,
        Raid.cover_image_url,
        # ST_X/ST_Y need geometry, but `loc` is geography — cast first.
        func.ST_Y(loc.cast(Geometry)).cast(Float).label("latitude"),
        func.ST_X(loc.cast(Geometry)).cast(Float).label("longitude"),
        distance.label("distance_m"),
        participant_count.label("participant_count"),
        my_rsvp.label("my_rsvp"),
        _drink_match_expr(viewer_id).label("drink_match"),
    )


# --------------------------------------------------------------------------- #
# Listing
# --------------------------------------------------------------------------- #
async def list_raids(
    db: AsyncSession, viewer_id: int, params: RaidListParams
) -> tuple[list[RaidRead], int]:
    cols = _raid_columns(
        viewer_id=viewer_id, near_lat=params.near_lat, near_lon=params.near_lon
    )
    stmt = (
        select(*cols)
        .select_from(Raid)
        .outerjoin(Bar, Bar.id == Raid.bar_id)
    )
    count_stmt = select(func.count(Raid.id)).select_from(Raid).outerjoin(Bar, Bar.id == Raid.bar_id)

    # Hide friends-only raids from strangers.
    vis = _visibility_filter(viewer_id)
    stmt = stmt.where(vis)
    count_stmt = count_stmt.where(vis)

    if params.scope == "mine":
        my_raids = exists().where(
            RaidParticipant.raid_id == Raid.id,
            RaidParticipant.user_id == viewer_id,
        )
        organised = Raid.organizer_id == viewer_id
        stmt = stmt.where(or_(my_raids, organised))
        count_stmt = count_stmt.where(or_(my_raids, organised))

    if params.status is not None:
        stmt = stmt.where(Raid.status == params.status)
        count_stmt = count_stmt.where(Raid.status == params.status)

    if (
        params.near_lat is not None
        and params.near_lon is not None
        and params.radius_m is not None
    ):
        loc = _raid_location_expr()
        point = func.ST_SetSRID(
            func.ST_MakePoint(params.near_lon, params.near_lat), 4326
        )
        geo_filter = func.ST_DWithin(loc, point, params.radius_m)
        stmt = stmt.where(geo_filter, loc.is_not(None))
        count_stmt = count_stmt.where(geo_filter, loc.is_not(None))
        # Nearest first, then taste (drink) match floats matching events up.
        stmt = stmt.order_by(asc("distance_m"), desc("drink_match"))
    else:
        # Default: upcoming first, then taste match as a soft tiebreaker.
        stmt = stmt.order_by(
            case((Raid.scheduled_at >= func.now(), 0), else_=1),
            Raid.scheduled_at.asc(),
            desc("drink_match"),
        )

    stmt = stmt.limit(params.limit).offset(params.offset)

    rows = (await db.execute(stmt)).all()
    total = (await db.execute(count_stmt)).scalar_one()
    drinks = await _drink_types_for(db, [r[0] for r in rows])
    return (
        [_row_to_read(r, viewer_id=viewer_id, drink_types=drinks.get(r[0], [])) for r in rows],
        int(total),
    )


async def get_raid(db: AsyncSession, viewer_id: int, raid_id: int) -> RaidRead:
    cols = _raid_columns(viewer_id=viewer_id, near_lat=None, near_lon=None)
    stmt = (
        select(*cols)
        .select_from(Raid)
        .outerjoin(Bar, Bar.id == Raid.bar_id)
        .where(Raid.id == raid_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        raise NotFoundError("raid not found")
    drinks = await _drink_types_for(db, [raid_id])
    read = _row_to_read(row, viewer_id=viewer_id, drink_types=drinks.get(raid_id, []))
    # Friends-only raids are invisible to non-friends/non-participants.
    if read.visibility == "friends_only" and read.organizer_id != viewer_id:
        allowed = (
            await db.execute(select(_visibility_filter(viewer_id)).where(Raid.id == raid_id))
        ).scalar_one_or_none()
        if not allowed:
            raise NotFoundError("raid not found")
    return read


# --------------------------------------------------------------------------- #
# Create / update / cancel
# --------------------------------------------------------------------------- #
async def create_raid(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    *,
    organizer_id: int,
    payload: RaidCreate,
) -> RaidRead:
    if payload.bar_id is not None:
        bar = await db.get(Bar, payload.bar_id)
        if bar is None or bar.deleted_at is not None:
            raise BadRequestError("bar_id refers to a missing bar")

    location_expr = None
    if payload.latitude is not None and payload.longitude is not None:
        location_expr = func.ST_SetSRID(
            func.ST_MakePoint(payload.longitude, payload.latitude), 4326
        )

    raid = Raid(
        title=payload.title,
        description=payload.description,
        bar_id=payload.bar_id,
        organizer_id=organizer_id,
        location=location_expr,
        scheduled_at=payload.scheduled_at,
        ends_at=payload.ends_at,
        max_participants=payload.max_participants,
        theme=payload.theme,
        visibility=payload.visibility,
        cover_image_url=payload.cover_image_url,
    )
    db.add(raid)
    await db.flush()

    # Organiser is auto-RSVP'd
    db.add(
        RaidParticipant(raid_id=raid.id, user_id=organizer_id, status="going")
    )
    for dt in sorted(set(payload.drink_types)):
        db.add(RaidDrink(raid_id=raid.id, drink_type=dt))

    await db.commit()

    # Fire notifications to invitees
    for uid in payload.invite_user_ids:
        if uid == organizer_id:
            continue
        try:
            await notifications_service.create_and_deliver(
                db, redis, push,
                recipient_id=uid,
                sender_id=organizer_id,
                type="raid_invite",
                title="You've been invited on a raid",
                body=raid.title,
                data={"raid_id": raid.id},
                related_entity_type="raid",
                related_entity_id=raid.id,
            )
        except Exception:  # noqa: BLE001 — best-effort per recipient
            continue

    return await get_raid(db, organizer_id, raid.id)


async def update_raid(
    db: AsyncSession, actor_id: int, raid_id: int, payload: RaidUpdate
) -> RaidRead:
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.organizer_id != actor_id:
        raise ForbiddenError("only the organiser can update a raid")

    data = payload.model_dump(exclude_unset=True)
    drink_types = data.pop("drink_types", None)
    for k, v in data.items():
        setattr(raid, k, v)

    if drink_types is not None:
        await db.execute(delete(RaidDrink).where(RaidDrink.raid_id == raid_id))
        for dt in sorted(set(drink_types)):
            db.add(RaidDrink(raid_id=raid_id, drink_type=dt))

    await db.commit()
    return await get_raid(db, actor_id, raid_id)


async def cancel_raid(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    actor_id: int,
    raid_id: int,
) -> RaidRead:
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.organizer_id != actor_id:
        raise ForbiddenError("only the organiser can cancel a raid")
    if raid.status == "cancelled":
        return await get_raid(db, actor_id, raid_id)
    raid.status = "cancelled"
    await db.commit()

    # Tell each going/maybe participant
    rows = (
        await db.execute(
            select(RaidParticipant.user_id).where(
                RaidParticipant.raid_id == raid_id,
                RaidParticipant.status.in_(("going", "maybe")),
                RaidParticipant.user_id != actor_id,
            )
        )
    ).scalars().all()
    for uid in rows:
        try:
            await notifications_service.create_and_deliver(
                db, redis, push,
                recipient_id=uid,
                sender_id=actor_id,
                type="raid_reminder",
                title="Raid cancelled",
                body=raid.title,
                data={"raid_id": raid_id, "status": "cancelled"},
                related_entity_type="raid",
                related_entity_id=raid_id,
            )
        except Exception:  # noqa: BLE001
            continue

    return await get_raid(db, actor_id, raid_id)


# --------------------------------------------------------------------------- #
# RSVP
# --------------------------------------------------------------------------- #
async def set_rsvp(
    db: AsyncSession, user_id: int, raid_id: int, status: str
) -> RaidRead:
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.status == "cancelled":
        raise ConflictError("raid is cancelled")

    # Double-booking guard: can't commit as `going` to two raids whose time
    # windows overlap. `maybe`/`declined` don't count as a commitment.
    if status == "going":
        this_start, this_end = _window(raid.scheduled_at, raid.ends_at)
        others = (
            await db.execute(
                select(Raid.scheduled_at, Raid.ends_at)
                .join(
                    RaidParticipant,
                    RaidParticipant.raid_id == Raid.id,
                )
                .where(
                    RaidParticipant.user_id == user_id,
                    RaidParticipant.status.in_(("going", "arrived")),
                    Raid.id != raid_id,
                    Raid.status.notin_(("cancelled", "aborted", "completed")),
                )
            )
        ).all()
        for other_start, other_end in others:
            o_start, o_end = _window(other_start, other_end)
            if o_start < this_end and this_start < o_end:
                raise ConflictError(
                    "you're already committed to another raid at this time"
                )

    # Capacity check (only when joining as going)
    if status == "going" and raid.max_participants is not None:
        going_count = (
            await db.execute(
                select(func.count(RaidParticipant.user_id)).where(
                    RaidParticipant.raid_id == raid_id,
                    RaidParticipant.status == "going",
                )
            )
        ).scalar_one()

        # An existing 'going' from this user doesn't count against capacity
        if (
            await db.get(RaidParticipant, (raid_id, user_id))
        ) is None or going_count >= raid.max_participants:
            if int(going_count) >= raid.max_participants:
                raise ConflictError("raid is full")

    row = await db.get(RaidParticipant, (raid_id, user_id))
    if row is None:
        row = RaidParticipant(raid_id=raid_id, user_id=user_id, status=status)
        db.add(row)
    else:
        row.status = status
    await db.commit()

    return await get_raid(db, user_id, raid_id)


# --------------------------------------------------------------------------- #
# Roster
# --------------------------------------------------------------------------- #
async def list_participants(
    db: AsyncSession, viewer_id: int, raid_id: int
) -> list[RaidParticipantDetail]:
    """Everyone on the raid, with display info — used by the host's
    verification screen. Visibility is enforced via get_raid first."""
    await get_raid(db, viewer_id, raid_id)  # raises if not visible / missing
    rows = (
        await db.execute(
            select(
                RaidParticipant.user_id,
                User.username,
                User.first_name,
                User.avatar_url,
                RaidParticipant.status,
                RaidParticipant.arrived_at,
                RaidParticipant.verified_at,
            )
            .join(User, User.id == RaidParticipant.user_id)
            .where(RaidParticipant.raid_id == raid_id)
            .order_by(RaidParticipant.joined_at.asc())
        )
    ).all()
    return [
        RaidParticipantDetail(
            user_id=uid,
            username=username,
            first_name=first_name,
            avatar_url=avatar_url,
            status=status,
            arrived_at=arrived_at,
            verified_at=verified_at,
        )
        for (uid, username, first_name, avatar_url, status, arrived_at, verified_at) in rows
    ]


# --------------------------------------------------------------------------- #
# Lifecycle: checkpoint → verify → complete / abort
# --------------------------------------------------------------------------- #
async def checkpoint(db: AsyncSession, user_id: int, raid_id: int) -> RaidRead:
    """Participant marks themselves on-site. Moves their RSVP `going` →
    `arrived` and flips the raid to `ongoing` on the first arrival."""
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.status in ("cancelled", "aborted", "completed"):
        raise ConflictError("raid is not active")

    row = await db.get(RaidParticipant, (raid_id, user_id))
    if row is None or row.status not in ("going", "arrived"):
        raise BadRequestError("you must be going to this raid to check in")

    if row.status == "going":
        row.status = "arrived"
        row.arrived_at = datetime.now(UTC)
    if raid.status == "planned":
        raid.status = "ongoing"
    await db.commit()
    return await get_raid(db, user_id, raid_id)


async def verify_attendance(
    db: AsyncSession, actor_id: int, raid_id: int, payload: RaidVerify
) -> RaidRead:
    """Host confirms who actually showed up. Each verdict updates the
    participant's RSVP and nudges their social rating + lifetime counters."""
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.organizer_id != actor_id:
        raise ForbiddenError("only the organiser can verify attendance")
    if raid.status in ("cancelled", "aborted"):
        raise ConflictError("raid is not active")

    now = datetime.now(UTC)
    for mark in payload.marks:
        if mark.user_id == raid.organizer_id:
            continue  # the host's own attendance isn't scored
        part = await db.get(RaidParticipant, (raid_id, mark.user_id))
        if part is None:
            raise BadRequestError(f"user {mark.user_id} is not on this raid")
        if part.verified_at is not None:
            continue  # idempotent — already scored, don't double-count

        part.status = mark.verdict
        part.verified_at = now

        attendee = await db.get(User, mark.user_id)
        if attendee is None:
            continue
        if mark.verdict == "attended":
            attendee.events_attended = (attendee.events_attended or 0) + 1
            attendee.social_rating = _clamp_rating(
                (attendee.social_rating or 0) + RATING_ATTENDED_DELTA
            )
        else:  # no_show
            attendee.events_ditched = (attendee.events_ditched or 0) + 1
            attendee.social_rating = _clamp_rating(
                (attendee.social_rating or 0) + RATING_NO_SHOW_DELTA
            )

    await db.commit()
    return await get_raid(db, actor_id, raid_id)


async def complete_raid(db: AsyncSession, actor_id: int, raid_id: int) -> RaidRead:
    """Host wraps the raid up. Any going/arrived participant the host never
    verified is treated as a no-show so the rating engine stays honest."""
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.organizer_id != actor_id:
        raise ForbiddenError("only the organiser can complete a raid")
    if raid.status in ("cancelled", "aborted"):
        raise ConflictError("raid is not active")
    if raid.status == "completed":
        return await get_raid(db, actor_id, raid_id)

    now = datetime.now(UTC)
    unverified = (
        await db.execute(
            select(RaidParticipant).where(
                RaidParticipant.raid_id == raid_id,
                RaidParticipant.user_id != raid.organizer_id,
                RaidParticipant.verified_at.is_(None),
                RaidParticipant.status.in_(("going", "arrived")),
            )
        )
    ).scalars().all()
    for part in unverified:
        part.status = "no_show"
        part.verified_at = now
        attendee = await db.get(User, part.user_id)
        if attendee is not None:
            attendee.events_ditched = (attendee.events_ditched or 0) + 1
            attendee.social_rating = _clamp_rating(
                (attendee.social_rating or 0) + RATING_NO_SHOW_DELTA
            )

    raid.status = "completed"
    await db.commit()
    return await get_raid(db, actor_id, raid_id)


async def abort_raid(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    actor_id: int,
    raid_id: int,
) -> RaidRead:
    """Host kills a raid that already started. Unlike `complete`, nobody is
    scored — an aborted raid is a non-event for everyone's rating."""
    raid = await db.get(Raid, raid_id)
    if raid is None:
        raise NotFoundError("raid not found")
    if raid.organizer_id != actor_id:
        raise ForbiddenError("only the organiser can abort a raid")
    if raid.status in ("cancelled", "aborted", "completed"):
        raise ConflictError("raid is not active")

    raid.status = "aborted"
    await db.commit()

    rows = (
        await db.execute(
            select(RaidParticipant.user_id).where(
                RaidParticipant.raid_id == raid_id,
                RaidParticipant.status.in_(("going", "maybe", "arrived")),
                RaidParticipant.user_id != actor_id,
            )
        )
    ).scalars().all()
    for uid in rows:
        try:
            await notifications_service.create_and_deliver(
                db, redis, push,
                recipient_id=uid,
                sender_id=actor_id,
                type="raid_reminder",
                title="Raid called off",
                body=raid.title,
                data={"raid_id": raid_id, "status": "aborted"},
                related_entity_type="raid",
                related_entity_id=raid_id,
            )
        except Exception:  # noqa: BLE001
            continue

    return await get_raid(db, actor_id, raid_id)


# Re-exported to satisfy linters
__all__ = [
    "list_raids", "get_raid", "create_raid", "update_raid",
    "cancel_raid", "set_rsvp", "list_participants",
    "checkpoint", "verify_attendance", "complete_raid", "abort_raid",
    "and_", "asc", "datetime", "UTC",
]
