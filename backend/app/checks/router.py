"""Checks (receipts) + split-room + dice router."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status

from app.checks import service
from app.checks.schemas import (
    CheckCreate,
    CheckRead,
    DiceProposalRead,
    DiceVoteCast,
    EventCheckCreate,
    InviteParticipants,
    ItemAssignmentUpsert,
    KindSoulEventRead,
    KindSoulLeaderRow,
    ReceiptUploadRequest,
    ReceiptUploadResponse,
)
from app.core.deps import CurrentUser, DbSession
from app.core.redis import get_redis
from app.services.ocr import OcrService
from app.services.push import PushService
from app.services.registry import get_ocr_service, get_push_service, get_storage_service
from app.services.storage import StorageService

router = APIRouter(prefix="/checks", tags=["checks"])

OcrDep = Annotated[OcrService, Depends(get_ocr_service)]
PushDep = Annotated[PushService, Depends(get_push_service)]
StorageDep = Annotated[StorageService, Depends(get_storage_service)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


@router.post("/upload-url", response_model=ReceiptUploadResponse)
async def receipt_upload_url(
    payload: ReceiptUploadRequest, user: CurrentUser, storage: StorageDep
) -> ReceiptUploadResponse:
    """Hand back a presigned PUT URL the phone uploads the receipt photo to.

    The returned `public_url` is what the client then passes to POST /checks
    as `image_url`, so the server-side Vision call can fetch the image.
    """
    presigned = await storage.presign_upload(
        prefix=f"receipts/{user.id}", content_type=payload.content_type
    )
    return ReceiptUploadResponse(
        upload_url=presigned.upload_url,
        public_url=presigned.public_url,
        key=presigned.key,
        expires_in=presigned.expires_in,
    )


# --------------------------------------------------------------------------- #
# Create / list / detail
# --------------------------------------------------------------------------- #
@router.post("", response_model=CheckRead, status_code=status.HTTP_201_CREATED)
async def create_check(
    payload: CheckCreate, db: DbSession, user: CurrentUser, ocr: OcrDep
) -> CheckRead:
    return await service.create_check(
        db, ocr, user,
        image_url=payload.image_url, bar_id=payload.bar_id,
        occurred_at=payload.occurred_at, note=payload.note,
    )


@router.post(
    "/from-event", response_model=CheckRead, status_code=status.HTTP_201_CREATED
)
async def create_event_check(
    payload: EventCheckCreate,
    db: DbSession,
    user: CurrentUser,
    ocr: OcrDep,
    redis: RedisDep,
    push: PushDep,
) -> CheckRead:
    """Open a split room from a finished raid/party's shared bill, seeded with
    the event's verified attendees."""
    return await service.create_event_check(
        db, ocr, redis, push, user,
        image_url=payload.image_url,
        raid_id=payload.raid_id,
        party_id=payload.party_id,
        occurred_at=payload.occurred_at,
        note=payload.note,
    )


@router.get("", response_model=list[CheckRead])
async def list_my_checks(
    db: DbSession, user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CheckRead]:
    return await service.list_my_checks(db, user.id, limit=limit, offset=offset)


@router.get("/{check_id}", response_model=CheckRead)
async def get_check(check_id: int, db: DbSession, user: CurrentUser) -> CheckRead:
    return await service.get_check(db, user.id, check_id)


# --------------------------------------------------------------------------- #
# Invite / join / leave / ready
# --------------------------------------------------------------------------- #
@router.post("/{check_id}/invite", response_model=CheckRead)
async def invite(
    check_id: int, payload: InviteParticipants,
    db: DbSession, user: CurrentUser, redis: RedisDep, push: PushDep,
) -> CheckRead:
    return await service.invite_participants(
        db, redis, push,
        actor=user, check_id=check_id,
        user_ids=payload.user_ids, guests=payload.guests,
    )


@router.post("/{check_id}/join", response_model=CheckRead)
async def join(check_id: int, db: DbSession, user: CurrentUser, redis: RedisDep) -> CheckRead:
    return await service.join_room(db, redis, user.id, check_id)


@router.post("/{check_id}/leave", response_model=CheckRead)
async def leave(check_id: int, db: DbSession, user: CurrentUser, redis: RedisDep) -> CheckRead:
    return await service.leave_room(db, redis, user.id, check_id)


@router.post("/{check_id}/ready", response_model=CheckRead)
async def ready(check_id: int, db: DbSession, user: CurrentUser, redis: RedisDep) -> CheckRead:
    return await service.set_ready(db, redis, user.id, check_id, ready=True)


@router.post("/{check_id}/unready", response_model=CheckRead)
async def unready(check_id: int, db: DbSession, user: CurrentUser, redis: RedisDep) -> CheckRead:
    return await service.set_ready(db, redis, user.id, check_id, ready=False)


# --------------------------------------------------------------------------- #
# Item assignments
# --------------------------------------------------------------------------- #
@router.put(
    "/{check_id}/items/{item_id}/assignments",
    response_model=CheckRead,
)
async def upsert_assignment(
    check_id: int, item_id: int, payload: ItemAssignmentUpsert,
    db: DbSession, user: CurrentUser, redis: RedisDep,
) -> CheckRead:
    return await service.upsert_assignment(
        db, redis,
        actor_id=user.id, check_id=check_id, item_id=item_id,
        participant_id=payload.participant_id, quantity=Decimal(payload.quantity),
    )


@router.delete(
    "/{check_id}/items/{item_id}/assignments/{participant_id}",
    response_model=CheckRead,
)
async def remove_assignment(
    check_id: int, item_id: int, participant_id: int,
    db: DbSession, user: CurrentUser, redis: RedisDep,
) -> CheckRead:
    return await service.remove_assignment(
        db, redis,
        actor_id=user.id, check_id=check_id, item_id=item_id, participant_id=participant_id,
    )


# --------------------------------------------------------------------------- #
# Dice game
# --------------------------------------------------------------------------- #
@router.post("/{check_id}/dice/propose", response_model=DiceProposalRead)
async def propose_dice(
    check_id: int, db: DbSession, user: CurrentUser, redis: RedisDep
) -> DiceProposalRead:
    return await service.propose_dice(db, redis, actor_id=user.id, check_id=check_id)


@router.post("/{check_id}/dice/{proposal_id}/vote")
async def vote_dice(
    check_id: int, proposal_id: int, payload: DiceVoteCast,
    db: DbSession, user: CurrentUser, redis: RedisDep, push: PushDep,
) -> DiceProposalRead | KindSoulEventRead:
    return await service.vote_dice(
        db, redis, push, actor_id=user.id, proposal_id=proposal_id, vote=payload.vote
    )


@router.get("/_/kind-soul/leaderboard", response_model=list[KindSoulLeaderRow])
async def leaderboard(
    db: DbSession, limit: int = Query(default=20, ge=1, le=100)
) -> list[KindSoulLeaderRow]:
    return await service.kind_soul_leaderboard(db, limit=limit)
