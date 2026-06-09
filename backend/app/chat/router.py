"""Chat router."""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status

from app.chat import service
from app.chat.schemas import (
    ConversationCreate,
    ConversationRead,
    MarkReadRequest,
    MessageCreate,
    MessageEdit,
    MessageRead,
    PresenceRead,
    ReactionToggle,
)
from app.core.deps import CurrentUser, DbSession
from app.core.redis import get_redis

router = APIRouter(prefix="/chat", tags=["chat"])

RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


# --------------------------------------------------------------------------- #
# Conversations
# --------------------------------------------------------------------------- #
@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    db: DbSession, user: CurrentUser
) -> list[ConversationRead]:
    return await service.list_my_conversations(db, user.id)


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate, db: DbSession, user: CurrentUser
) -> ConversationRead:
    return await service.create_conversation(db, user.id, payload)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: int, db: DbSession, user: CurrentUser
) -> ConversationRead:
    return await service.get_conversation(db, user.id, conversation_id)


# --------------------------------------------------------------------------- #
# Messages
# --------------------------------------------------------------------------- #
@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageRead],
)
async def list_messages(
    conversation_id: int,
    db: DbSession,
    user: CurrentUser,
    before_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[MessageRead]:
    return await service.list_messages(
        db, user.id, conversation_id, before_id=before_id, limit=limit
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int, payload: MessageCreate,
    db: DbSession, user: CurrentUser, redis: RedisDep,
) -> MessageRead:
    return await service.send_message(
        db, redis,
        sender_id=user.id, conversation_id=conversation_id, payload=payload,
    )


@router.patch("/messages/{message_id}", response_model=MessageRead)
async def edit_message(
    message_id: int, payload: MessageEdit,
    db: DbSession, user: CurrentUser, redis: RedisDep,
) -> MessageRead:
    return await service.edit_message(
        db, redis, user_id=user.id, message_id=message_id, body=payload.body
    )


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int, db: DbSession, user: CurrentUser, redis: RedisDep,
) -> None:
    await service.delete_message(db, redis, user_id=user.id, message_id=message_id)


@router.post(
    "/messages/{message_id}/reactions",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def toggle_reaction(
    message_id: int, payload: ReactionToggle,
    db: DbSession, user: CurrentUser, redis: RedisDep,
) -> None:
    await service.toggle_reaction(
        db, redis, user_id=user.id, message_id=message_id, emoji=payload.emoji,
    )


# --------------------------------------------------------------------------- #
# Read receipts
# --------------------------------------------------------------------------- #
@router.post(
    "/conversations/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_read(
    conversation_id: int, payload: MarkReadRequest,
    db: DbSession, user: CurrentUser, redis: RedisDep,
) -> None:
    await service.mark_read_up_to(
        db, redis,
        user_id=user.id, conversation_id=conversation_id,
        up_to_message_id=payload.up_to_message_id,
    )


# --------------------------------------------------------------------------- #
# Presence
# --------------------------------------------------------------------------- #
@router.get("/presence", response_model=list[PresenceRead])
async def presence(
    db: DbSession,
    user: CurrentUser,
    user_ids: list[int] = Query(default_factory=list),
) -> list[PresenceRead]:
    # Always include self
    ids = list({user.id, *user_ids})
    return await service.get_presence_many(db, ids)
