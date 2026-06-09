"""
Checks service — receipt upload + split room + dice.

The collaborative split-room flow is the most multi-device part of the app.
Every state transition that other participants need to see is broadcast on
the `check:{check_id}` Redis channel, which any open WebSocket subscribed
to that room picks up via the pub/sub bridge.

Lifecycle (high level):
    create_check        — upload image, OCR, persist items, add host as joined participant.
    invite              — add registered/guest participants, push `check_invite` notif.
    join                — invitee opens the room, status invited → joined.
    leave               — status → left (any time).
    upsert_assignment   — pick "I had 1 of these" on an item.
    set_ready           — status → ready when done assigning.
    propose_dice        — open unanimous-consent vote for D20 game.
    vote_dice           — accept/decline. On all-accept the dice rolls; on any
                          decline the proposal is closed.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.bars.models import Bar
from app.checks.models import (
    Check,
    CheckItem,
    CheckItemAssignment,
    CheckParticipant,
    DiceProposal,
    DiceProposalVote,
    KindSoulEvent,
)
from app.checks.schemas import (
    CheckItemRead,
    CheckParticipantRead,
    CheckRead,
    DiceProposalRead,
    DiceVoteRead,
    KindSoulEventRead,
    KindSoulLeaderRow,
)
from app.notifications import service as notifications_service
from app.parties.models import Party, PartyMember
from app.raids.models import Raid, RaidParticipant
from app.services.ocr import OcrService
from app.services.push import PushService
from app.shared.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


CHECK_CHANNEL_PREFIX = "check:"


def _check_channel(check_id: int) -> str:
    return f"{CHECK_CHANNEL_PREFIX}{check_id}"


async def _publish(redis: aioredis.Redis, check_id: int, event: dict[str, Any]) -> None:
    """Fan an event out to every connected device in the split room."""
    await redis.publish(_check_channel(check_id), json.dumps(event, default=str))


# --------------------------------------------------------------------------- #
# Lookup / serialisation
# --------------------------------------------------------------------------- #
async def _load_full(db: AsyncSession, check_id: int) -> CheckRead:
    check = await db.get(Check, check_id)
    if check is None or check.deleted_at is not None:
        raise NotFoundError("check not found")

    items = (
        await db.execute(
            select(CheckItem).where(CheckItem.check_id == check_id).order_by(CheckItem.position)
        )
    ).scalars().all()

    participants = (
        await db.execute(
            select(CheckParticipant).where(CheckParticipant.check_id == check_id)
        )
    ).scalars().all()

    # Compute assigned-quantity per item
    item_assignments = (
        await db.execute(
            select(
                CheckItemAssignment.check_item_id,
                func.sum(CheckItemAssignment.quantity),
            )
            .join(CheckItem, CheckItem.id == CheckItemAssignment.check_item_id)
            .where(CheckItem.check_id == check_id)
            .group_by(CheckItemAssignment.check_item_id)
        )
    ).all()
    assigned_qty: dict[int, Decimal] = {iid: q for iid, q in item_assignments}

    # Compute subtotal per participant
    subtotals = (
        await db.execute(
            select(
                CheckItemAssignment.participant_id,
                func.sum(CheckItemAssignment.amount),
            )
            .join(CheckParticipant, CheckParticipant.id == CheckItemAssignment.participant_id)
            .where(CheckParticipant.check_id == check_id)
            .group_by(CheckItemAssignment.participant_id)
        )
    ).all()
    sub_by_pid: dict[int, Decimal] = {pid: total for pid, total in subtotals}

    item_reads = [
        CheckItemRead.model_validate(
            {**i.__dict__, "assigned_quantity": assigned_qty.get(i.id, Decimal("0"))}
        )
        for i in items
    ]
    participant_reads = [
        CheckParticipantRead.model_validate(
            {**p.__dict__, "subtotal": sub_by_pid.get(p.id, Decimal("0"))}
        )
        for p in participants
    ]
    return CheckRead(
        id=check.id,
        user_id=check.user_id,
        bar_id=check.bar_id,
        raid_id=check.raid_id,
        party_id=check.party_id,
        bar_name_freeform=check.bar_name_freeform,
        currency=check.currency,
        total_amount=check.total_amount,
        image_url=check.image_url,
        occurred_at=check.occurred_at,
        note=check.note,
        parsed_at=check.parsed_at,
        created_at=check.created_at,
        items=item_reads,
        participants=participant_reads,
    )


def _require_participant_user(
    participants: list[CheckParticipant], user_id: int
) -> CheckParticipant:
    """Raise 403 if user isn't a registered participant in this check."""
    for p in participants:
        if p.user_id == user_id and p.status != "left":
            return p
    raise ForbiddenError("not a participant in this check")


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #
async def create_check(
    db: AsyncSession, ocr: OcrService, user: User, *, image_url: str,
    bar_id: int | None, occurred_at: datetime | None, note: str | None,
) -> CheckRead:
    if bar_id is not None:
        if (await db.get(Bar, bar_id)) is None:
            raise BadRequestError("bar_id refers to a missing bar")

    parsed = await ocr.parse_receipt(image_url)

    check = Check(
        user_id=user.id,
        bar_id=bar_id,
        bar_name_freeform=parsed.bar_name if bar_id is None else None,
        currency=parsed.currency,
        total_amount=parsed.total_amount,
        image_url=image_url,
        ocr_payload=parsed.raw,
        parsed_at=datetime.now(tz=UTC),
        occurred_at=occurred_at,
        note=note,
    )
    db.add(check)
    await db.flush()

    for pos, item in enumerate(parsed.items):
        db.add(
            CheckItem(
                check_id=check.id,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                position=pos,
            )
        )

    # Host joins automatically.
    db.add(
        CheckParticipant(
            check_id=check.id,
            user_id=user.id,
            display_name=user.first_name,
            status="joined",
            joined_at=datetime.now(tz=UTC),
        )
    )
    await db.commit()
    return await _load_full(db, check.id)


# --------------------------------------------------------------------------- #
# Create from a finished event (raid / party shared bill) — WP5
# --------------------------------------------------------------------------- #
async def _event_attendee_ids(
    db: AsyncSession, *, raid_id: int | None, party_id: int | None, host_id: int
) -> list[int]:
    """The users who count as "at the table" for an event's shared bill.

    Raid → participants the host verified as `attended`.
    Party → members currently `joined`.
    The host is excluded here (they're added separately as the room owner).
    """
    if raid_id is not None:
        rows = (
            await db.execute(
                select(RaidParticipant.user_id).where(
                    RaidParticipant.raid_id == raid_id,
                    RaidParticipant.status == "attended",
                    RaidParticipant.user_id != host_id,
                )
            )
        ).scalars().all()
        return list(rows)
    rows = (
        await db.execute(
            select(PartyMember.user_id).where(
                PartyMember.party_id == party_id,
                PartyMember.status == "joined",
                PartyMember.user_id != host_id,
            )
        )
    ).scalars().all()
    return list(rows)


async def create_event_check(
    db: AsyncSession,
    ocr: OcrService,
    redis: aioredis.Redis,
    push: PushService,
    user: User,
    *,
    image_url: str,
    raid_id: int | None,
    party_id: int | None,
    occurred_at: datetime | None,
    note: str | None,
) -> CheckRead:
    """Host photographs the single shared bill after a raid/party; OCR parses
    it and a split room is opened, pre-seeded with everyone who showed up. Each
    attendee gets a "select what you ordered" nudge."""
    if (raid_id is None) == (party_id is None):
        raise BadRequestError("exactly one of raid_id or party_id is required")

    # Authorise the host and make sure we don't double-create a bill.
    if raid_id is not None:
        raid = await db.get(Raid, raid_id)
        if raid is None:
            raise NotFoundError("raid not found")
        if raid.organizer_id != user.id:
            raise ForbiddenError("only the host can split this raid's bill")
        dup = (
            await db.execute(
                select(Check.id).where(
                    Check.raid_id == raid_id, Check.deleted_at.is_(None)
                )
            )
        ).scalar_one_or_none()
        if dup is not None:
            raise ConflictError("this raid already has a shared bill")
    else:
        party = await db.get(Party, party_id)
        if party is None:
            raise NotFoundError("party not found")
        if party.host_id != user.id:
            raise ForbiddenError("only the host can split this party's bill")
        dup = (
            await db.execute(
                select(Check.id).where(
                    Check.party_id == party_id, Check.deleted_at.is_(None)
                )
            )
        ).scalar_one_or_none()
        if dup is not None:
            raise ConflictError("this party already has a shared bill")

    attendee_ids = await _event_attendee_ids(
        db, raid_id=raid_id, party_id=party_id, host_id=user.id
    )

    parsed = await ocr.parse_receipt(image_url)
    now = datetime.now(tz=UTC)

    check = Check(
        user_id=user.id,
        bar_id=None,
        raid_id=raid_id,
        party_id=party_id,
        bar_name_freeform=parsed.bar_name,
        currency=parsed.currency,
        total_amount=parsed.total_amount,
        image_url=image_url,
        ocr_payload=parsed.raw,
        parsed_at=now,
        occurred_at=occurred_at,
        note=note,
    )
    db.add(check)
    await db.flush()

    for pos, item in enumerate(parsed.items):
        db.add(
            CheckItem(
                check_id=check.id,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                position=pos,
            )
        )

    # Host owns the room.
    db.add(
        CheckParticipant(
            check_id=check.id,
            user_id=user.id,
            display_name=user.first_name,
            status="joined",
            joined_at=now,
        )
    )

    # Attendees are invited to pick their items (dedupe + unique display name).
    seen_users = {user.id}
    seen_names = {user.first_name}
    for uid in attendee_ids:
        if uid in seen_users:
            continue
        u = await db.get(User, uid)
        if u is None:
            continue
        display = u.first_name
        if display in seen_names:
            display = f"{display} ({u.username})"
        db.add(
            CheckParticipant(
                check_id=check.id,
                user_id=uid,
                display_name=display,
                status="invited",
            )
        )
        seen_users.add(uid)
        seen_names.add(display)

    await db.commit()

    # "Select what you ordered" nudge to each invited attendee.
    invited = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == check.id,
                CheckParticipant.status == "invited",
                CheckParticipant.user_id.is_not(None),
            )
        )
    ).scalars().all()
    for p in invited:
        try:
            await notifications_service.create_and_deliver(
                db, redis, push,
                recipient_id=p.user_id,
                sender_id=user.id,
                type="check_invite",
                title="Time to split the bill",
                body=f"{user.first_name} scanned the receipt — select what you ordered",
                data={"check_id": check.id, "participant_id": p.id},
                related_entity_type="check",
                related_entity_id=check.id,
            )
        except Exception:  # noqa: BLE001
            continue

    return await _load_full(db, check.id)


# --------------------------------------------------------------------------- #
# Listing / detail
# --------------------------------------------------------------------------- #
async def get_check(db: AsyncSession, user_id: int, check_id: int) -> CheckRead:
    check = await _load_full(db, check_id)
    # Only the owner OR a participant can read.
    if check.user_id != user_id and not any(
        p.user_id == user_id for p in check.participants
    ):
        raise ForbiddenError("you don't have access to this check")
    return check


async def list_my_checks(db: AsyncSession, user_id: int, limit: int, offset: int) -> list[CheckRead]:
    rows = (
        await db.execute(
            select(Check.id)
            .where(Check.user_id == user_id, Check.deleted_at.is_(None))
            .order_by(Check.created_at.desc())
            .limit(limit).offset(offset)
        )
    ).scalars().all()
    return [await _load_full(db, cid) for cid in rows]


# --------------------------------------------------------------------------- #
# Invite / join / leave / ready
# --------------------------------------------------------------------------- #
async def invite_participants(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    *,
    actor: User,
    check_id: int,
    user_ids: list[int],
    guests: list[str],
) -> CheckRead:
    check = await db.get(Check, check_id)
    if check is None or check.deleted_at is not None:
        raise NotFoundError("check not found")
    if check.user_id != actor.id:
        raise ForbiddenError("only the host can invite to a check")

    existing = (
        await db.execute(
            select(CheckParticipant).where(CheckParticipant.check_id == check_id)
        )
    ).scalars().all()
    seen_users = {p.user_id for p in existing if p.user_id is not None}
    seen_names = {p.display_name for p in existing}

    # Registered invitees
    for uid in user_ids:
        if uid in seen_users or uid == actor.id:
            continue
        u = await db.get(User, uid)
        if u is None:
            continue
        display = u.first_name
        if display in seen_names:
            display = f"{display} ({u.username})"
        db.add(
            CheckParticipant(
                check_id=check_id, user_id=u.id, display_name=display, status="invited"
            )
        )
        seen_users.add(uid)
        seen_names.add(display)

    # Guests
    for name in guests:
        if not name.strip() or name in seen_names:
            continue
        db.add(
            CheckParticipant(
                check_id=check_id,
                user_id=None,
                display_name=name.strip(),
                status="joined",
                joined_at=datetime.now(tz=UTC),
            )
        )
        seen_names.add(name)

    await db.commit()
    await _publish(redis, check_id, {"type": "participants.changed", "check_id": check_id})

    # Send `check_invite` notifications to newly invited registered users.
    new_invited = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == check_id,
                CheckParticipant.user_id.in_(user_ids) if user_ids else False,
                CheckParticipant.status == "invited",
            )
        )
    ).scalars().all()
    for p in new_invited:
        if p.user_id is None:
            continue
        try:
            await notifications_service.create_and_deliver(
                db, redis, push,
                recipient_id=p.user_id,
                sender_id=actor.id,
                type="check_invite",
                title="You were invited to split a receipt",
                body=f"{actor.first_name} wants you to chip in",
                data={"check_id": check_id, "participant_id": p.id},
                related_entity_type="check",
                related_entity_id=check_id,
            )
        except Exception:  # noqa: BLE001
            continue

    return await _load_full(db, check_id)


async def join_room(
    db: AsyncSession, redis: aioredis.Redis, user_id: int, check_id: int
) -> CheckRead:
    p = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == check_id,
                CheckParticipant.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if p is None:
        raise ForbiddenError("you weren't invited")
    if p.status == "left":
        # Re-joining after leaving is allowed if the room is still open.
        p.status = "joined"
        p.joined_at = datetime.now(tz=UTC)
        p.left_at = None
    elif p.status == "invited":
        p.status = "joined"
        p.joined_at = datetime.now(tz=UTC)
    await db.commit()
    await _publish(redis, check_id, {"type": "participant.joined", "user_id": user_id})
    return await _load_full(db, check_id)


async def leave_room(
    db: AsyncSession, redis: aioredis.Redis, user_id: int, check_id: int
) -> CheckRead:
    p = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == check_id,
                CheckParticipant.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if p is None:
        raise ForbiddenError("you are not in this room")
    p.status = "left"
    p.left_at = datetime.now(tz=UTC)
    # If a dice proposal was pending and this user was a voter, cancel it.
    pending = (
        await db.execute(
            select(DiceProposal).where(
                DiceProposal.check_id == check_id, DiceProposal.status == "pending"
            )
        )
    ).scalar_one_or_none()
    if pending is not None:
        voter = await db.get(DiceProposalVote, (pending.id, user_id))
        if voter is not None:
            pending.status = "cancelled"
            pending.cancel_reason = f"voter {user_id} left the room"
            pending.decided_at = datetime.now(tz=UTC)
    await db.commit()
    await _publish(redis, check_id, {"type": "participant.left", "user_id": user_id})
    return await _load_full(db, check_id)


async def set_ready(
    db: AsyncSession, redis: aioredis.Redis, user_id: int, check_id: int, *, ready: bool
) -> CheckRead:
    p = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == check_id,
                CheckParticipant.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if p is None:
        raise ForbiddenError("you are not in this room")

    if ready:
        p.status = "ready"
        p.ready_at = datetime.now(tz=UTC)
    else:
        if p.status != "ready":
            return await _load_full(db, check_id)
        p.status = "joined"
        p.ready_at = None
    await db.commit()
    await _publish(
        redis, check_id,
        {"type": "participant.ready" if ready else "participant.unready", "user_id": user_id},
    )
    return await _load_full(db, check_id)


# --------------------------------------------------------------------------- #
# Assignments
# --------------------------------------------------------------------------- #
async def upsert_assignment(
    db: AsyncSession, redis: aioredis.Redis, *, actor_id: int, check_id: int,
    item_id: int, participant_id: int, quantity: Decimal,
) -> CheckRead:
    item = await db.get(CheckItem, item_id)
    if item is None or item.check_id != check_id:
        raise NotFoundError("item not found in this check")

    participant = await db.get(CheckParticipant, participant_id)
    if participant is None or participant.check_id != check_id:
        raise NotFoundError("participant not found in this check")

    # Must be the participant themselves OR the host who created the check.
    check = await db.get(Check, check_id)
    if check is None:
        raise NotFoundError("check not found")
    if participant.user_id != actor_id and check.user_id != actor_id:
        raise ForbiddenError("you can only assign items to yourself")

    # Don't exceed the item's available quantity.
    already = (
        await db.execute(
            select(func.coalesce(func.sum(CheckItemAssignment.quantity), 0))
            .where(
                CheckItemAssignment.check_item_id == item_id,
                CheckItemAssignment.participant_id != participant_id,
            )
        )
    ).scalar_one() or Decimal("0")
    if quantity + Decimal(already) > item.quantity:
        raise ConflictError("assigned quantity exceeds item quantity")

    amount = quantity * item.unit_price

    existing = await db.get(CheckItemAssignment, (item_id, participant_id))
    if existing is None:
        db.add(
            CheckItemAssignment(
                check_item_id=item_id,
                participant_id=participant_id,
                quantity=quantity,
                amount=amount,
            )
        )
    else:
        existing.quantity = quantity
        existing.amount = amount
    await db.commit()

    await _publish(
        redis, check_id,
        {
            "type": "assignment.updated",
            "check_item_id": item_id,
            "participant_id": participant_id,
            "quantity": str(quantity),
            "amount": str(amount),
        },
    )
    return await _load_full(db, check_id)


async def remove_assignment(
    db: AsyncSession, redis: aioredis.Redis, *, actor_id: int, check_id: int,
    item_id: int, participant_id: int,
) -> CheckRead:
    existing = await db.get(CheckItemAssignment, (item_id, participant_id))
    if existing is None:
        return await _load_full(db, check_id)

    participant = await db.get(CheckParticipant, participant_id)
    check = await db.get(Check, check_id)
    if (
        participant is None
        or check is None
        or (participant.user_id != actor_id and check.user_id != actor_id)
    ):
        raise ForbiddenError("forbidden")

    await db.delete(existing)
    await db.commit()
    await _publish(
        redis, check_id,
        {
            "type": "assignment.removed",
            "check_item_id": item_id,
            "participant_id": participant_id,
        },
    )
    return await _load_full(db, check_id)


# --------------------------------------------------------------------------- #
# Dice game — unanimous consent → D20 → kind_soul
# --------------------------------------------------------------------------- #
async def propose_dice(
    db: AsyncSession, redis: aioredis.Redis, *, actor_id: int, check_id: int
) -> DiceProposalRead:
    """Open a unanimous-consent vote. Caller must be a registered participant."""
    check = await db.get(Check, check_id)
    if check is None:
        raise NotFoundError("check not found")
    participants = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == check_id,
                CheckParticipant.user_id.is_not(None),
                CheckParticipant.status.in_(("joined", "ready")),
            )
        )
    ).scalars().all()
    if not any(p.user_id == actor_id for p in participants):
        raise ForbiddenError("only registered participants can propose")

    # Any open proposal?
    pending = (
        await db.execute(
            select(DiceProposal).where(
                DiceProposal.check_id == check_id, DiceProposal.status == "pending"
            )
        )
    ).scalar_one_or_none()
    if pending is not None:
        raise ConflictError("a dice proposal is already pending")

    proposal = DiceProposal(check_id=check_id, proposed_by=actor_id)
    db.add(proposal)
    await db.flush()

    # Insert votes — proposer auto-accepts, everyone else 'pending'.
    for p in participants:
        if p.user_id is None:
            continue
        db.add(
            DiceProposalVote(
                proposal_id=proposal.id,
                user_id=p.user_id,
                vote="accept" if p.user_id == actor_id else "pending",
                voted_at=datetime.now(tz=UTC) if p.user_id == actor_id else None,
            )
        )
    await db.commit()
    await _publish(
        redis, check_id,
        {"type": "dice.proposal.created", "proposal_id": proposal.id, "proposed_by": actor_id},
    )
    return await get_proposal(db, proposal.id)


async def get_proposal(db: AsyncSession, proposal_id: int) -> DiceProposalRead:
    proposal = await db.get(DiceProposal, proposal_id)
    if proposal is None:
        raise NotFoundError("proposal not found")
    votes = (
        await db.execute(
            select(DiceProposalVote).where(DiceProposalVote.proposal_id == proposal_id)
        )
    ).scalars().all()
    return DiceProposalRead.model_validate(
        {
            **proposal.__dict__,
            "votes": [DiceVoteRead.model_validate(v.__dict__) for v in votes],
        }
    )


async def vote_dice(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    *,
    actor_id: int,
    proposal_id: int,
    vote: str,
) -> DiceProposalRead | KindSoulEventRead:
    proposal = await db.get(DiceProposal, proposal_id)
    if proposal is None:
        raise NotFoundError("proposal not found")
    if proposal.status != "pending":
        raise ConflictError("proposal is not pending")

    vote_row = await db.get(DiceProposalVote, (proposal_id, actor_id))
    if vote_row is None:
        raise ForbiddenError("you are not eligible to vote on this proposal")
    vote_row.vote = vote
    vote_row.voted_at = datetime.now(tz=UTC)
    await db.flush()

    # Decision?
    votes = (
        await db.execute(
            select(DiceProposalVote.vote).where(DiceProposalVote.proposal_id == proposal_id)
        )
    ).scalars().all()
    if any(v == "decline" for v in votes):
        proposal.status = "declined"
        proposal.decided_at = datetime.now(tz=UTC)
        await db.commit()
        await _publish(
            redis, proposal.check_id,
            {"type": "dice.proposal.declined", "proposal_id": proposal_id},
        )
        return await get_proposal(db, proposal_id)

    if all(v == "accept" for v in votes):
        proposal.status = "accepted"
        proposal.decided_at = datetime.now(tz=UTC)
        await db.flush()
        kind_soul = await _roll_dice_and_record(db, proposal)
        await db.commit()
        await _publish(
            redis, proposal.check_id,
            {
                "type": "dice.completed",
                "proposal_id": proposal_id,
                "payer_user_id": kind_soul.payer_user_id,
                "total_paid_for_others": str(kind_soul.total_paid_for_others),
            },
        )

        # Notify everyone in the room of the outcome.
        rolls_meta = kind_soul.event_metadata
        for uid in (rolls_meta.get("rolls", {}) or {}).keys():
            try:
                await notifications_service.create_and_deliver(
                    db, redis, push,
                    recipient_id=int(uid),
                    sender_id=proposal.proposed_by,
                    type="kind_soul_awarded" if int(uid) == kind_soul.payer_user_id else "dice_proposal_resolved",
                    title="Kind Soul!" if int(uid) == kind_soul.payer_user_id else "Dice roll done",
                    body=f"₴{kind_soul.total_paid_for_others} for the table"
                         if int(uid) == kind_soul.payer_user_id
                         else "Result is in — open the receipt",
                    data={
                        "check_id": proposal.check_id,
                        "payer_user_id": kind_soul.payer_user_id,
                    },
                    related_entity_type="check",
                    related_entity_id=proposal.check_id,
                )
            except Exception:  # noqa: BLE001
                continue
        return KindSoulEventRead.model_validate(
            {
                **kind_soul.__dict__,
                "event_metadata": kind_soul.event_metadata,
            }
        )

    # Still waiting for someone to vote.
    await db.commit()
    return await get_proposal(db, proposal_id)


async def _roll_dice_and_record(
    db: AsyncSession, proposal: DiceProposal
) -> KindSoulEvent:
    """Roll a d20 per registered participant, highest wins; record kind_soul."""
    voters = (
        await db.execute(
            select(DiceProposalVote.user_id).where(
                DiceProposalVote.proposal_id == proposal.id,
                DiceProposalVote.vote == "accept",
            )
        )
    ).scalars().all()
    if not voters:
        raise BadRequestError("no eligible voters for the dice roll")

    rolls: dict[int, int] = {int(uid): random.randint(1, 20) for uid in voters}  # noqa: S311
    # Highest roll wins; tie → first id (deterministic).
    winner_id = sorted(rolls.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

    participant = (
        await db.execute(
            select(CheckParticipant).where(
                CheckParticipant.check_id == proposal.check_id,
                CheckParticipant.user_id == winner_id,
            )
        )
    ).scalar_one()

    # Total the winner pays for OTHERS (their own subtotal excluded).
    total_others = (
        await db.execute(
            select(func.coalesce(func.sum(CheckItemAssignment.amount), 0))
            .join(CheckParticipant, CheckParticipant.id == CheckItemAssignment.participant_id)
            .where(
                CheckParticipant.check_id == proposal.check_id,
                CheckParticipant.id != participant.id,
            )
        )
    ).scalar_one() or Decimal("0")

    event = KindSoulEvent(
        check_id=proposal.check_id,
        proposal_id=proposal.id,
        payer_user_id=winner_id,
        payer_participant_id=participant.id,
        total_paid_for_others=Decimal(total_others),
        decided_via="d20_dice",
        event_metadata={"rolls": rolls, "winner_id": winner_id},
        occurred_at=datetime.now(tz=UTC),
    )
    db.add(event)

    proposal.status = "completed"
    return event


# --------------------------------------------------------------------------- #
# Leaderboard
# --------------------------------------------------------------------------- #
async def kind_soul_leaderboard(
    db: AsyncSession, limit: int = 20
) -> list[KindSoulLeaderRow]:
    rows = (
        await db.execute(
            select(
                User.id,
                User.first_name,
                User.username,
                User.avatar_url,
                func.count(KindSoulEvent.id).label("events_count"),
                func.coalesce(func.sum(KindSoulEvent.total_paid_for_others), 0).label("total"),
            )
            .join(KindSoulEvent, KindSoulEvent.payer_user_id == User.id)
            .group_by(User.id)
            .order_by(func.sum(KindSoulEvent.total_paid_for_others).desc())
            .limit(limit)
        )
    ).all()
    return [
        KindSoulLeaderRow(
            user_id=uid,
            first_name=first,
            username=username,
            avatar_url=avatar,
            events_count=int(count),
            total_paid_for_others=Decimal(total),
        )
        for uid, first, username, avatar, count, total in rows
    ]
