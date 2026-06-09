"""
Tavern Tales service — characters, sessions, turns, quota.

A "turn" is the round-trip: the user submits a free-text action; we
construct a chat-history prompt (system + recent messages + summary),
call the LLM service, persist both messages, and update the session's
token counters + the per-user quota. If the user is over quota the
request is rejected with a 429.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.services.llm import LlmReply, LlmService
from app.shared.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.tavern_tales.models import (
    DndCharacter,
    DndClassInfo,
    DndMessage,
    DndSession,
    DndUsageQuota,
)
from app.tavern_tales.schemas import (
    CharacterCreate,
    CharacterRead,
    CharacterUpdate,
    DndClassInfoRead,
    MessageRead,
    QuotaRead,
    SessionRead,
    TurnResponse,
)


# --------------------------------------------------------------------------- #
# Class info
# --------------------------------------------------------------------------- #
async def list_classes(db: AsyncSession) -> list[DndClassInfoRead]:
    rows = (
        await db.execute(select(DndClassInfo).order_by(DndClassInfo.name))
    ).scalars().all()
    return [DndClassInfoRead.model_validate(r) for r in rows]


# --------------------------------------------------------------------------- #
# Characters
# --------------------------------------------------------------------------- #
async def list_characters(
    db: AsyncSession, user_id: int
) -> list[CharacterRead]:
    rows = (
        await db.execute(
            select(DndCharacter)
            .where(DndCharacter.user_id == user_id, DndCharacter.deleted_at.is_(None))
            .order_by(DndCharacter.last_played_at.desc().nullslast())
        )
    ).scalars().all()
    return [CharacterRead.model_validate(c) for c in rows]


async def create_character(
    db: AsyncSession, user: User, payload: CharacterCreate
) -> CharacterRead:
    # Character race is the user's quiz race; users must have taken the quiz.
    if user.race_id is None:
        raise BadRequestError("take the race quiz before creating a character")

    if (await db.get(DndClassInfo, payload.class_slug)) is None:
        raise BadRequestError("unknown class_slug")

    char = DndCharacter(
        user_id=user.id,
        race_id=user.race_id,
        class_slug=payload.class_slug,
        name=payload.name,
        alignment=payload.alignment,
        stats=payload.stats or {},
        background=payload.background,
        avatar_url=payload.avatar_url,
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)
    return CharacterRead.model_validate(char)


async def get_character(
    db: AsyncSession, user_id: int, character_id: int
) -> CharacterRead:
    c = await db.get(DndCharacter, character_id)
    if c is None or c.deleted_at is not None or c.user_id != user_id:
        raise NotFoundError("character not found")
    return CharacterRead.model_validate(c)


async def update_character(
    db: AsyncSession, user_id: int, character_id: int, payload: CharacterUpdate
) -> CharacterRead:
    c = await db.get(DndCharacter, character_id)
    if c is None or c.deleted_at is not None or c.user_id != user_id:
        raise NotFoundError("character not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    await db.commit()
    await db.refresh(c)
    return CharacterRead.model_validate(c)


async def delete_character(
    db: AsyncSession, user_id: int, character_id: int
) -> None:
    c = await db.get(DndCharacter, character_id)
    if c is None or c.deleted_at is not None or c.user_id != user_id:
        raise NotFoundError("character not found")
    c.deleted_at = datetime.now(tz=UTC)
    c.is_active = False
    await db.commit()


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
async def create_session(
    db: AsyncSession, user_id: int, character_id: int, mode: str, title: str | None
) -> SessionRead:
    char = await db.get(DndCharacter, character_id)
    if char is None or char.deleted_at is not None or char.user_id != user_id:
        raise NotFoundError("character not found")

    # Reject if there's already an in-progress quest for this character
    in_progress = (
        await db.execute(
            select(DndSession).where(
                DndSession.character_id == character_id,
                DndSession.status.in_(("active", "paused")),
            )
        )
    ).scalar_one_or_none()
    if in_progress is not None:
        raise ConflictError("this character already has an in-progress session")

    sess = DndSession(character_id=character_id, mode=mode, title=title)
    db.add(sess)
    await db.commit()
    await db.refresh(sess)
    return SessionRead.model_validate(sess)


async def list_sessions(
    db: AsyncSession, user_id: int, character_id: int
) -> list[SessionRead]:
    char = await db.get(DndCharacter, character_id)
    if char is None or char.user_id != user_id:
        raise NotFoundError("character not found")
    rows = (
        await db.execute(
            select(DndSession)
            .where(DndSession.character_id == character_id)
            .order_by(DndSession.started_at.desc())
        )
    ).scalars().all()
    return [SessionRead.model_validate(s) for s in rows]


async def list_messages(
    db: AsyncSession, user_id: int, session_id: int
) -> list[MessageRead]:
    sess = await db.get(DndSession, session_id)
    if sess is None:
        raise NotFoundError("session not found")
    char = await db.get(DndCharacter, sess.character_id)
    if char is None or char.user_id != user_id:
        raise ForbiddenError("not your session")

    rows = (
        await db.execute(
            select(DndMessage)
            .where(DndMessage.session_id == session_id)
            .order_by(DndMessage.created_at)
        )
    ).scalars().all()
    return [MessageRead.model_validate(m) for m in rows]


# --------------------------------------------------------------------------- #
# Quota
# --------------------------------------------------------------------------- #
async def _ensure_quota(db: AsyncSession, user_id: int) -> DndUsageQuota:
    quota = await db.get(DndUsageQuota, user_id)
    today = date.today()
    if quota is None:
        quota = DndUsageQuota(
            user_id=user_id,
            daily_reset_at=today,
            monthly_reset_at=today.replace(day=1),
        )
        db.add(quota)
        await db.flush()

    # Roll over counters if a boundary was crossed
    if quota.daily_reset_at < today:
        quota.daily_tokens_used = 0
        quota.daily_reset_at = today
    if quota.monthly_reset_at < today.replace(day=1):
        quota.monthly_tokens_used = 0
        quota.monthly_reset_at = today.replace(day=1)
    return quota


async def get_quota(db: AsyncSession, user_id: int) -> QuotaRead:
    quota = await _ensure_quota(db, user_id)
    await db.commit()
    return QuotaRead.model_validate(quota)


# --------------------------------------------------------------------------- #
# Turn
# --------------------------------------------------------------------------- #
def _build_prompt(
    character: DndCharacter,
    session: DndSession,
    history: list[DndMessage],
    user_input: str,
) -> list[dict[str, str]]:
    """Compose the chat-completion messages array for an LLM call."""
    mode_brief = {
        "munchkin": "Be playful, silly, very generous with loot. Casual tone.",
        "normal": "Run a standard 5e-flavoured adventure with balanced challenges.",
        "dungeon_master_pro": "Strict, atmospheric DM. Lethal but fair.",
    }.get(session.mode, "")

    system = (
        "You are a Dungeon Master narrating a D&D 5e session for a single player. "
        f"Style: {mode_brief}. "
        f"The player character is {character.name} (level {character.level} {character.class_slug}). "
        f"HP {character.hp_current}/{character.hp_max}, AC {character.armor_class}. "
        "Reply with vivid prose. If the player should roll, end with a JSON block: "
        '{"request_roll":{"dice":"d20","dc":15,"purpose":"persuasion"}}.'
    )
    if session.summary:
        system += f"\nStory so far: {session.summary}"

    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in history[-20:]:
        if m.role in ("user", "assistant", "system"):
            msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": user_input})
    return msgs


async def take_turn(
    db: AsyncSession, llm: LlmService, user: User, session_id: int, content: str
) -> TurnResponse:
    sess = await db.get(DndSession, session_id)
    if sess is None:
        raise NotFoundError("session not found")
    if sess.status not in ("active", "paused"):
        raise ConflictError("session is not active")

    character = await db.get(DndCharacter, sess.character_id)
    if character is None or character.user_id != user.id:
        raise ForbiddenError("not your session")

    # Quota gate
    quota = await _ensure_quota(db, user.id)
    if (
        quota.daily_tokens_used >= quota.daily_tokens_limit
        or quota.monthly_tokens_used >= quota.monthly_tokens_limit
    ):
        from fastapi import HTTPException, status as http_status  # local import — rare path
        raise HTTPException(
            status_code=http_status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"quota": QuotaRead.model_validate(quota).model_dump()},
        )

    history = (
        await db.execute(
            select(DndMessage)
            .where(DndMessage.session_id == session_id)
            .order_by(DndMessage.created_at)
        )
    ).scalars().all()

    user_msg = DndMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    prompt = _build_prompt(character, sess, history, content)
    reply: LlmReply = await llm.chat_completion(prompt)

    assistant_msg = DndMessage(
        session_id=session_id,
        role="assistant",
        content=reply.content,
        message_metadata=reply.metadata or {},
        tokens_in=reply.tokens_in,
        tokens_out=reply.tokens_out,
    )
    db.add(assistant_msg)

    # Update counters
    used = reply.tokens_in + reply.tokens_out
    sess.input_tokens_used += reply.tokens_in
    sess.output_tokens_used += reply.tokens_out
    sess.turn_count += 1
    sess.last_message_at = datetime.now(tz=UTC)
    character.last_played_at = datetime.now(tz=UTC)
    quota.daily_tokens_used += used
    quota.monthly_tokens_used += used

    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)
    await db.refresh(sess)

    return TurnResponse(
        user_message=MessageRead.model_validate(user_msg),
        assistant_message=MessageRead.model_validate(assistant_msg),
        session=SessionRead.model_validate(sess),
    )


async def record_dice_roll(
    db: AsyncSession, user_id: int, session_id: int,
    *, dice: str, modifier: int, result: int, purpose: str | None,
) -> MessageRead:
    sess = await db.get(DndSession, session_id)
    if sess is None:
        raise NotFoundError("session not found")
    character = await db.get(DndCharacter, sess.character_id)
    if character is None or character.user_id != user_id:
        raise ForbiddenError("not your session")

    msg = DndMessage(
        session_id=session_id,
        role="dice_roll",
        content=f"{dice}{'+' if modifier >= 0 else ''}{modifier} = {result}",
        message_metadata={
            "dice": dice, "modifier": modifier,
            "result": result, "purpose": purpose,
        },
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return MessageRead.model_validate(msg)


async def end_session(
    db: AsyncSession, user_id: int, session_id: int, *, status: str = "completed"
) -> SessionRead:
    sess = await db.get(DndSession, session_id)
    if sess is None:
        raise NotFoundError("session not found")
    char = await db.get(DndCharacter, sess.character_id)
    if char is None or char.user_id != user_id:
        raise ForbiddenError("not your session")
    if sess.status not in ("active", "paused"):
        return SessionRead.model_validate(sess)
    if status not in ("completed", "abandoned", "paused"):
        raise BadRequestError("invalid status")

    sess.status = status
    sess.ended_at = datetime.now(tz=UTC) if status != "paused" else None
    await db.commit()
    await db.refresh(sess)
    return SessionRead.model_validate(sess)


# Re-exports for linters
__all__ = [
    "list_classes", "list_characters", "create_character", "get_character",
    "update_character", "delete_character", "create_session", "list_sessions",
    "list_messages", "get_quota", "take_turn", "record_dice_roll", "end_session",
    "Any",
]
