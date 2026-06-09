"""
Achievements service.

`evaluate_event` is called from other domains when something happens that
could unlock an achievement: a receipt is created, a quiz finishes, a raid
completes, a kind_soul event occurs. The function looks up active
achievements whose `requirement` matches the event type, bumps the user's
progress, and awards the badge once the threshold is crossed.

This keeps the rules out of the calling code — each domain just emits the
event type plus a tiny payload and forgets about it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.achievements.models import Achievement, UserAchievement
from app.achievements.schemas import AchievementRead, UserAchievementRead
from app.notifications import service as notifications_service
from app.services.push import PushService

# --------------------------------------------------------------------------- #
# Read API
# --------------------------------------------------------------------------- #
async def list_all(db: AsyncSession) -> list[AchievementRead]:
    rows = (
        await db.execute(
            select(Achievement).where(Achievement.is_active.is_(True)).order_by(
                Achievement.category, Achievement.points
            )
        )
    ).scalars().all()
    return [AchievementRead.model_validate(r) for r in rows]


async def list_for_user(
    db: AsyncSession, user_id: int
) -> list[UserAchievementRead]:
    rows = (
        await db.execute(
            select(Achievement, UserAchievement)
            .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.awarded_at.desc())
        )
    ).all()
    return [
        UserAchievementRead(
            achievement=AchievementRead.model_validate(a),
            awarded_at=ua.awarded_at,
            progress=ua.progress or {},
        )
        for a, ua in rows
    ]


# --------------------------------------------------------------------------- #
# Event evaluation
# --------------------------------------------------------------------------- #
async def evaluate_event(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    *,
    user_id: int,
    event_type: str,
    delta: int = 1,
    extra: dict[str, Any] | None = None,
) -> list[AchievementRead]:
    """
    Bump progress on every active achievement whose `requirement.type`
    equals `event_type`. Awarded achievements are returned so the caller
    can include them in the response.

    Examples of (event_type, requirement):
        check_count_increment    -> {"type": "check_count", "threshold": N}
        kind_soul_increment      -> {"type": "kind_soul_count", "threshold": N}
        kind_soul_total          -> {"type": "kind_soul_total", "threshold": amount}
        raid_completed           -> {"type": "raid_count", "threshold": N}
        quiz_completed           -> {"type": "quiz_completed"}        # one-shot
        friend_added             -> {"type": "friend_count", "threshold": N}
    """
    extra = extra or {}
    requirement_key = event_type.replace("_increment", "").replace("_completed", "_completed")

    candidates = (
        await db.execute(
            select(Achievement).where(
                Achievement.is_active.is_(True),
                Achievement.requirement["type"].astext == requirement_key,
            )
        )
    ).scalars().all()

    awarded: list[AchievementRead] = []
    for ach in candidates:
        ua = await db.get(UserAchievement, (user_id, ach.id))
        if ua is not None and ua.progress.get("awarded"):
            continue

        threshold = int(ach.requirement.get("threshold", 1))
        current = int((ua.progress or {}).get("count", 0)) if ua else 0
        new_count = current + delta

        progress: dict[str, Any] = {"count": new_count}
        unlocked = new_count >= threshold
        if unlocked:
            progress["awarded"] = True

        if ua is None:
            db.add(
                UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    awarded_at=datetime.now(tz=UTC),
                    progress=progress,
                )
            )
        else:
            ua.progress = progress
            ua.awarded_at = datetime.now(tz=UTC)

        if unlocked:
            awarded.append(AchievementRead.model_validate(ach))
            try:
                await notifications_service.create_and_deliver(
                    db, redis, push,
                    recipient_id=user_id,
                    type="achievement_unlocked",
                    title=f"Achievement unlocked: {ach.name}",
                    body=ach.description,
                    data={"achievement_id": ach.id, "code": ach.code},
                    related_entity_type="achievement",
                    related_entity_id=ach.id,
                )
            except Exception:  # noqa: BLE001
                pass

    await db.commit()
    return awarded


# --------------------------------------------------------------------------- #
# Stats helper
# --------------------------------------------------------------------------- #
async def points_total(db: AsyncSession, user_id: int) -> int:
    total = (
        await db.execute(
            select(func.coalesce(func.sum(Achievement.points), 0))
            .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
            .where(
                UserAchievement.user_id == user_id,
                UserAchievement.progress["awarded"].astext == "true",
            )
        )
    ).scalar_one()
    return int(total)
