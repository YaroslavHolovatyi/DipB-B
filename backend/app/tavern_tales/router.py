"""Tavern Tales (D&D AI DM) router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DbSession
from app.services.llm import LlmService
from app.services.registry import get_llm_service
from app.tavern_tales import service
from app.tavern_tales.schemas import (
    CharacterCreate,
    CharacterRead,
    CharacterUpdate,
    DiceRoll,
    DndClassInfoRead,
    MessageRead,
    QuotaRead,
    SessionCreate,
    SessionRead,
    TurnResponse,
    UserTurn,
)

router = APIRouter(prefix="/tavern", tags=["tavern-tales"])

LlmDep = Annotated[LlmService, Depends(get_llm_service)]


# --------------------------------------------------------------------------- #
# Class info
# --------------------------------------------------------------------------- #
@router.get("/classes", response_model=list[DndClassInfoRead])
async def list_classes(db: DbSession) -> list[DndClassInfoRead]:
    return await service.list_classes(db)


# --------------------------------------------------------------------------- #
# Characters
# --------------------------------------------------------------------------- #
@router.get("/characters", response_model=list[CharacterRead])
async def list_characters(db: DbSession, user: CurrentUser) -> list[CharacterRead]:
    return await service.list_characters(db, user.id)


@router.post(
    "/characters",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_character(
    payload: CharacterCreate, db: DbSession, user: CurrentUser
) -> CharacterRead:
    return await service.create_character(db, user, payload)


@router.get("/characters/{character_id}", response_model=CharacterRead)
async def get_character(
    character_id: int, db: DbSession, user: CurrentUser
) -> CharacterRead:
    return await service.get_character(db, user.id, character_id)


@router.patch("/characters/{character_id}", response_model=CharacterRead)
async def update_character(
    character_id: int, payload: CharacterUpdate, db: DbSession, user: CurrentUser
) -> CharacterRead:
    return await service.update_character(db, user.id, character_id, payload)


@router.delete(
    "/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_character(
    character_id: int, db: DbSession, user: CurrentUser
) -> None:
    await service.delete_character(db, user.id, character_id)


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
@router.post(
    "/sessions",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    payload: SessionCreate, db: DbSession, user: CurrentUser
) -> SessionRead:
    return await service.create_session(
        db, user.id, payload.character_id, payload.mode, payload.title
    )


@router.get(
    "/characters/{character_id}/sessions", response_model=list[SessionRead]
)
async def list_sessions(
    character_id: int, db: DbSession, user: CurrentUser
) -> list[SessionRead]:
    return await service.list_sessions(db, user.id, character_id)


@router.get(
    "/sessions/{session_id}/messages", response_model=list[MessageRead]
)
async def list_messages(
    session_id: int, db: DbSession, user: CurrentUser
) -> list[MessageRead]:
    return await service.list_messages(db, user.id, session_id)


@router.post(
    "/sessions/{session_id}/turn", response_model=TurnResponse
)
async def take_turn(
    session_id: int, payload: UserTurn,
    db: DbSession, user: CurrentUser, llm: LlmDep,
) -> TurnResponse:
    return await service.take_turn(db, llm, user, session_id, payload.content)


@router.post(
    "/sessions/{session_id}/roll", response_model=MessageRead
)
async def roll_dice(
    session_id: int, payload: DiceRoll,
    db: DbSession, user: CurrentUser,
) -> MessageRead:
    return await service.record_dice_roll(
        db, user.id, session_id,
        dice=payload.dice, modifier=payload.modifier,
        result=payload.result, purpose=payload.purpose,
    )


@router.post(
    "/sessions/{session_id}/end", response_model=SessionRead
)
async def end_session(
    session_id: int, db: DbSession, user: CurrentUser,
    status_to: str = Query(default="completed", alias="status"),
) -> SessionRead:
    return await service.end_session(db, user.id, session_id, status=status_to)


# --------------------------------------------------------------------------- #
# Quota
# --------------------------------------------------------------------------- #
@router.get("/quota", response_model=QuotaRead)
async def get_quota(db: DbSession, user: CurrentUser) -> QuotaRead:
    return await service.get_quota(db, user.id)
