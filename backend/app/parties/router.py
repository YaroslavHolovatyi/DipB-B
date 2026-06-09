"""Parties router."""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbSession
from app.core.redis import get_redis
from app.parties import service
from app.parties.schemas import (
    PartyCreate,
    PartyInvite,
    PartyListParams,
    PartyMemberRead,
    PartyRead,
    PartyUpdate,
)
from app.services.push import PushService
from app.services.registry import get_push_service
from app.shared.pagination import Page

router = APIRouter(prefix="/parties", tags=["parties"])

PushDep = Annotated[PushService, Depends(get_push_service)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


@router.get("", response_model=Page[PartyRead])
async def list_parties(
    db: DbSession,
    user: CurrentUser,
    params: Annotated[PartyListParams, Depends()],
) -> Page[PartyRead]:
    items, total = await service.list_parties(db, user.id, params)
    return Page[PartyRead](
        items=items, total=total, limit=params.limit, offset=params.offset
    )


@router.post("", response_model=PartyRead, status_code=status.HTTP_201_CREATED)
async def create_party(
    payload: PartyCreate,
    db: DbSession,
    user: CurrentUser,
    redis: RedisDep,
    push: PushDep,
) -> PartyRead:
    return await service.create_party(
        db, redis, push, host_id=user.id, payload=payload
    )


@router.get("/{party_id}", response_model=PartyRead)
async def get_party(party_id: int, db: DbSession, user: CurrentUser) -> PartyRead:
    return await service.get_party(db, user.id, party_id)


@router.patch("/{party_id}", response_model=PartyRead)
async def update_party(
    party_id: int, payload: PartyUpdate, db: DbSession, user: CurrentUser
) -> PartyRead:
    return await service.update_party(db, user.id, party_id, payload)


@router.get("/{party_id}/members", response_model=list[PartyMemberRead])
async def list_members(
    party_id: int, db: DbSession, user: CurrentUser
) -> list[PartyMemberRead]:
    return await service.list_members(db, user.id, party_id)


@router.post("/{party_id}/join", response_model=PartyRead)
async def join_party(party_id: int, db: DbSession, user: CurrentUser) -> PartyRead:
    return await service.join_party(db, user.id, party_id)


@router.post("/{party_id}/leave", response_model=PartyRead)
async def leave_party(party_id: int, db: DbSession, user: CurrentUser) -> PartyRead:
    return await service.leave_party(db, user.id, party_id)


@router.post("/{party_id}/invite", response_model=PartyRead)
async def invite_to_party(
    party_id: int,
    payload: PartyInvite,
    db: DbSession,
    user: CurrentUser,
    redis: RedisDep,
    push: PushDep,
) -> PartyRead:
    return await service.invite_to_party(
        db, redis, push, user.id, party_id, payload.user_ids
    )
