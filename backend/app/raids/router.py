"""Raids router."""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbSession
from app.core.redis import get_redis
from app.raids import service
from app.raids.schemas import (
    RaidCreate,
    RaidListParams,
    RaidParticipantDetail,
    RaidRead,
    RaidRsvp,
    RaidUpdate,
    RaidVerify,
)
from app.services.push import PushService
from app.services.registry import get_push_service
from app.shared.pagination import Page

router = APIRouter(prefix="/raids", tags=["raids"])

PushDep = Annotated[PushService, Depends(get_push_service)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


@router.get("", response_model=Page[RaidRead])
async def list_raids(
    db: DbSession,
    user: CurrentUser,
    params: Annotated[RaidListParams, Depends()],
) -> Page[RaidRead]:
    items, total = await service.list_raids(db, user.id, params)
    return Page[RaidRead](
        items=items, total=total, limit=params.limit, offset=params.offset
    )


@router.post("", response_model=RaidRead, status_code=status.HTTP_201_CREATED)
async def create_raid(
    payload: RaidCreate,
    db: DbSession,
    user: CurrentUser,
    redis: RedisDep,
    push: PushDep,
) -> RaidRead:
    return await service.create_raid(
        db, redis, push, organizer_id=user.id, payload=payload
    )


@router.get("/{raid_id}", response_model=RaidRead)
async def get_raid(raid_id: int, db: DbSession, user: CurrentUser) -> RaidRead:
    return await service.get_raid(db, user.id, raid_id)


@router.patch("/{raid_id}", response_model=RaidRead)
async def update_raid(
    raid_id: int, payload: RaidUpdate, db: DbSession, user: CurrentUser
) -> RaidRead:
    return await service.update_raid(db, user.id, raid_id, payload)


@router.post("/{raid_id}/cancel", response_model=RaidRead)
async def cancel_raid(
    raid_id: int,
    db: DbSession,
    user: CurrentUser,
    redis: RedisDep,
    push: PushDep,
) -> RaidRead:
    return await service.cancel_raid(db, redis, push, user.id, raid_id)


@router.post("/{raid_id}/rsvp", response_model=RaidRead)
async def rsvp(
    raid_id: int, payload: RaidRsvp, db: DbSession, user: CurrentUser
) -> RaidRead:
    return await service.set_rsvp(db, user.id, raid_id, payload.status)


@router.get("/{raid_id}/participants", response_model=list[RaidParticipantDetail])
async def list_participants(
    raid_id: int, db: DbSession, user: CurrentUser
) -> list[RaidParticipantDetail]:
    """Roster with display info — powers the host verification screen."""
    return await service.list_participants(db, user.id, raid_id)


@router.post("/{raid_id}/checkpoint", response_model=RaidRead)
async def checkpoint(raid_id: int, db: DbSession, user: CurrentUser) -> RaidRead:
    """Participant checks in on-site (going → arrived)."""
    return await service.checkpoint(db, user.id, raid_id)


@router.post("/{raid_id}/verify", response_model=RaidRead)
async def verify(
    raid_id: int, payload: RaidVerify, db: DbSession, user: CurrentUser
) -> RaidRead:
    """Host confirms attendance for one or more participants."""
    return await service.verify_attendance(db, user.id, raid_id, payload)


@router.post("/{raid_id}/complete", response_model=RaidRead)
async def complete(raid_id: int, db: DbSession, user: CurrentUser) -> RaidRead:
    """Host wraps the raid up; unverified attendees count as no-shows."""
    return await service.complete_raid(db, user.id, raid_id)


@router.post("/{raid_id}/abort", response_model=RaidRead)
async def abort(
    raid_id: int,
    db: DbSession,
    user: CurrentUser,
    redis: RedisDep,
    push: PushDep,
) -> RaidRead:
    """Host kills an in-progress raid; nobody is scored."""
    return await service.abort_raid(db, redis, push, user.id, raid_id)
