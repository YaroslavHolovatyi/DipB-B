"""
Chat service.

Real-time delivery: every message insert publishes `message.new` on the
conversation's Redis channel, which fans out to every worker that hosts a
participant's WebSocket. The bridge maps the channel back to per-user
channels via the participant list, so the existing `user:*` subscription
on each worker delivers the frame.

Read receipts: `conversation_participants.last_read_at` is the watermark.
The client calls `POST /chat/conversations/{id}/read` with the newest
message id it has rendered; we set the watermark to that message's
`created_at`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReaction,
    UserPresence,
)
from app.chat.schemas import (
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
    PresenceRead,
)
from app.realtime.pubsub import publish_user
from app.shared.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
async def _broadcast_to_conversation(
    db: AsyncSession,
    redis: aioredis.Redis,
    conversation_id: int,
    event: dict[str, Any],
) -> None:
    """Publish an event on the per-user channel of every active participant."""
    user_ids = (
        await db.execute(
            select(ConversationParticipant.user_id).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.left_at.is_(None),
            )
        )
    ).scalars().all()
    for uid in user_ids:
        await publish_user(redis, uid, event)


def _attachments(attachments) -> list[dict]:  # type: ignore[no-untyped-def]
    """Accept either Pydantic Attachment models or raw dicts."""
    return [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in attachments]


# --------------------------------------------------------------------------- #
# Conversations
# --------------------------------------------------------------------------- #
async def find_or_create_direct(
    db: AsyncSession, viewer_id: int, other_id: int
) -> Conversation:
    """Find the existing direct conversation between (viewer, other) or create one."""
    if viewer_id == other_id:
        raise ConflictError("cannot start a direct chat with yourself")

    # Look for a direct conversation that has exactly these two participants.
    p1 = ConversationParticipant.__table__.alias("p1")
    p2 = ConversationParticipant.__table__.alias("p2")
    stmt = (
        select(Conversation.id)
        .join(p1, p1.c.conversation_id == Conversation.id)
        .join(p2, p2.c.conversation_id == Conversation.id)
        .where(
            Conversation.type == "direct",
            p1.c.user_id == viewer_id,
            p2.c.user_id == other_id,
            p1.c.left_at.is_(None),
            p2.c.left_at.is_(None),
        )
    )
    existing_id = (await db.execute(stmt)).scalar_one_or_none()
    if existing_id is not None:
        return (await db.execute(select(Conversation).where(Conversation.id == existing_id))).scalar_one()

    convo = Conversation(type="direct")
    db.add(convo)
    await db.flush()
    db.add_all([
        ConversationParticipant(conversation_id=convo.id, user_id=viewer_id),
        ConversationParticipant(conversation_id=convo.id, user_id=other_id),
    ])
    await db.commit()
    await db.refresh(convo)
    return convo


async def create_conversation(
    db: AsyncSession, viewer_id: int, payload: ConversationCreate
) -> ConversationRead:
    if payload.type == "direct":
        other = payload.participant_ids[0]
        convo = await find_or_create_direct(db, viewer_id, other)
        return await _as_read(db, viewer_id, convo)

    convo = Conversation(type="group", title=payload.title, friend_group_id=payload.friend_group_id)
    db.add(convo)
    await db.flush()

    members = {viewer_id, *payload.participant_ids}
    for uid in members:
        db.add(
            ConversationParticipant(
                conversation_id=convo.id, user_id=uid,
                role="admin" if uid == viewer_id else "member",
            )
        )
    await db.commit()
    await db.refresh(convo)
    return await _as_read(db, viewer_id, convo)


async def _as_read(
    db: AsyncSession, viewer_id: int, convo: Conversation
) -> ConversationRead:
    participants = (
        await db.execute(
            select(ConversationParticipant.user_id).where(
                ConversationParticipant.conversation_id == convo.id,
                ConversationParticipant.left_at.is_(None),
            )
        )
    ).scalars().all()

    viewer_p = await db.get(ConversationParticipant, (convo.id, viewer_id))
    unread = 0
    if viewer_p is not None:
        # `last_read_at` is a Python value here (we already loaded the row),
        # so we branch in Python instead of trying to build a SQL OR.
        where_clauses = [
            Message.conversation_id == convo.id,
            Message.sender_id != viewer_id,
            Message.deleted_at.is_(None),
        ]
        if viewer_p.last_read_at is not None:
            where_clauses.append(Message.created_at > viewer_p.last_read_at)

        unread = int(
            (
                await db.execute(select(func.count(Message.id)).where(*where_clauses))
            ).scalar_one()
            or 0
        )

    last_msg = (
        await db.execute(
            select(Message.body).where(
                Message.conversation_id == convo.id, Message.deleted_at.is_(None)
            ).order_by(Message.created_at.desc()).limit(1)
        )
    ).scalar_one_or_none()

    return ConversationRead(
        id=convo.id,
        type=convo.type,
        title=convo.title,
        image_url=convo.image_url,
        friend_group_id=convo.friend_group_id,
        raid_id=convo.raid_id,
        last_message_at=convo.last_message_at,
        participants=list(participants),
        unread_count=unread,
        last_message_preview=(last_msg[:120] if last_msg else None),
    )


async def list_my_conversations(
    db: AsyncSession, viewer_id: int
) -> list[ConversationRead]:
    convo_ids = (
        await db.execute(
            select(Conversation.id)
            .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
            .where(
                ConversationParticipant.user_id == viewer_id,
                ConversationParticipant.left_at.is_(None),
            )
            .order_by(Conversation.last_message_at.desc().nullslast())
        )
    ).scalars().all()
    out: list[ConversationRead] = []
    for cid in convo_ids:
        convo = await db.get(Conversation, cid)
        if convo is not None:
            out.append(await _as_read(db, viewer_id, convo))
    return out


async def get_conversation(
    db: AsyncSession, viewer_id: int, conversation_id: int
) -> ConversationRead:
    convo = await db.get(Conversation, conversation_id)
    if convo is None:
        raise NotFoundError("conversation not found")
    if (await db.get(ConversationParticipant, (conversation_id, viewer_id))) is None:
        raise ForbiddenError("not a participant of this conversation")
    return await _as_read(db, viewer_id, convo)


# --------------------------------------------------------------------------- #
# Messages
# --------------------------------------------------------------------------- #
async def list_messages(
    db: AsyncSession, viewer_id: int, conversation_id: int, *,
    before_id: int | None, limit: int,
) -> list[MessageRead]:
    if (await db.get(ConversationParticipant, (conversation_id, viewer_id))) is None:
        raise ForbiddenError("not a participant of this conversation")

    stmt = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id, Message.deleted_at.is_(None)
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    if before_id is not None:
        before = await db.get(Message, before_id)
        if before is not None:
            stmt = stmt.where(Message.created_at < before.created_at)

    rows = (await db.execute(stmt)).scalars().all()
    msgs = list(reversed(rows))

    # Load reactions in one query
    rxn_rows = (
        await db.execute(
            select(MessageReaction).where(MessageReaction.message_id.in_([m.id for m in msgs]))
        )
    ).scalars().all() if msgs else []
    rxn_map: dict[int, dict[str, list[int]]] = {}
    for r in rxn_rows:
        rxn_map.setdefault(r.message_id, {}).setdefault(r.emoji, []).append(r.user_id)

    return [
        MessageRead.model_validate(
            {
                **m.__dict__,
                "attachments": m.attachments or [],
                "reactions": rxn_map.get(m.id, {}),
            }
        )
        for m in msgs
    ]


async def send_message(
    db: AsyncSession, redis: aioredis.Redis, *,
    sender_id: int, conversation_id: int, payload: MessageCreate,
) -> MessageRead:
    if (await db.get(ConversationParticipant, (conversation_id, sender_id))) is None:
        raise ForbiddenError("not a participant of this conversation")

    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        body=payload.body,
        attachments=_attachments(payload.attachments),
        reply_to_id=payload.reply_to_id,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    payload_out = MessageRead.model_validate(
        {**msg.__dict__, "attachments": msg.attachments or [], "reactions": {}}
    ).model_dump(mode="json")

    await _broadcast_to_conversation(
        db, redis, conversation_id,
        {"type": "message.new", "data": payload_out},
    )
    return MessageRead.model_validate(payload_out)


async def edit_message(
    db: AsyncSession, redis: aioredis.Redis, *,
    user_id: int, message_id: int, body: str,
) -> MessageRead:
    msg = await db.get(Message, message_id)
    if msg is None or msg.deleted_at is not None:
        raise NotFoundError("message not found")
    if msg.sender_id != user_id:
        raise ForbiddenError("you can only edit your own messages")
    msg.body = body
    msg.edited_at = datetime.now(tz=UTC)
    await db.commit()
    await _broadcast_to_conversation(
        db, redis, msg.conversation_id,
        {"type": "message.updated", "message_id": message_id, "body": body},
    )
    return MessageRead.model_validate(
        {**msg.__dict__, "attachments": msg.attachments or [], "reactions": {}}
    )


async def delete_message(
    db: AsyncSession, redis: aioredis.Redis, *,
    user_id: int, message_id: int,
) -> None:
    msg = await db.get(Message, message_id)
    if msg is None or msg.deleted_at is not None:
        raise NotFoundError("message not found")
    if msg.sender_id != user_id:
        raise ForbiddenError("you can only delete your own messages")
    msg.deleted_at = datetime.now(tz=UTC)
    await db.commit()
    await _broadcast_to_conversation(
        db, redis, msg.conversation_id,
        {"type": "message.deleted", "message_id": message_id},
    )


# --------------------------------------------------------------------------- #
# Reactions
# --------------------------------------------------------------------------- #
async def toggle_reaction(
    db: AsyncSession, redis: aioredis.Redis, *,
    user_id: int, message_id: int, emoji: str,
) -> None:
    msg = await db.get(Message, message_id)
    if msg is None:
        raise NotFoundError("message not found")
    if (await db.get(ConversationParticipant, (msg.conversation_id, user_id))) is None:
        raise ForbiddenError("not a participant of this conversation")

    existing = await db.get(MessageReaction, (message_id, user_id, emoji))
    if existing is None:
        db.add(MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji))
        added = True
    else:
        await db.delete(existing)
        added = False
    await db.commit()

    await _broadcast_to_conversation(
        db, redis, msg.conversation_id,
        {
            "type": "reaction.toggled",
            "message_id": message_id, "user_id": user_id,
            "emoji": emoji, "added": added,
        },
    )


# --------------------------------------------------------------------------- #
# Read receipts
# --------------------------------------------------------------------------- #
async def mark_read_up_to(
    db: AsyncSession, redis: aioredis.Redis, *,
    user_id: int, conversation_id: int, up_to_message_id: int,
) -> None:
    p = await db.get(ConversationParticipant, (conversation_id, user_id))
    if p is None:
        raise ForbiddenError("not a participant")

    msg = await db.get(Message, up_to_message_id)
    if msg is None or msg.conversation_id != conversation_id:
        raise NotFoundError("message not in this conversation")

    if p.last_read_at is None or p.last_read_at < msg.created_at:
        p.last_read_at = msg.created_at
        await db.commit()
        await _broadcast_to_conversation(
            db, redis, conversation_id,
            {
                "type": "read.advanced",
                "user_id": user_id, "up_to_message_id": up_to_message_id,
            },
        )


# --------------------------------------------------------------------------- #
# Presence
# --------------------------------------------------------------------------- #
async def update_presence(
    db: AsyncSession, redis: aioredis.Redis, *,
    user_id: int, status: str,
) -> PresenceRead:
    p = await db.get(UserPresence, user_id)
    now = datetime.now(tz=UTC)
    if p is None:
        p = UserPresence(user_id=user_id, status=status, last_seen_at=now)
        db.add(p)
    else:
        p.status = status
        p.last_seen_at = now
    await db.commit()
    await db.refresh(p)
    # Tell friends so the green dot updates everywhere
    await publish_user(redis, user_id, {"type": "presence.self", "status": status})
    return PresenceRead.model_validate(p)


async def get_presence_many(
    db: AsyncSession, user_ids: list[int]
) -> list[PresenceRead]:
    if not user_ids:
        return []
    rows = (
        await db.execute(
            select(UserPresence).where(UserPresence.user_id.in_(user_ids))
        )
    ).scalars().all()
    return [PresenceRead.model_validate(r) for r in rows]


# Re-exports to satisfy linters
__all__ = [
    "find_or_create_direct", "create_conversation", "list_my_conversations",
    "get_conversation", "list_messages", "send_message", "edit_message",
    "delete_message", "toggle_reaction", "mark_read_up_to",
    "update_presence", "get_presence_many",
    "and_", "exists", "User",
]
