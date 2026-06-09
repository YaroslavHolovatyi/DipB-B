"""
Notifications service.

`create_and_deliver` is the workhorse — every other domain calls it when
something happens that needs to reach a user. It writes the row, publishes
a `notification.new` event to that user's Redis channel (so any open
WebSocket sees it immediately) and, if the user is offline, fires a single
Expo Push so the device wakes up.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification
from app.notifications.schemas import NotificationListParams, NotificationRead, UnreadCount
from app.realtime.manager import manager
from app.realtime.pubsub import publish_user
from app.services.push import PushMessage, PushService
from app.users.models import PushToken


# --------------------------------------------------------------------------- #
# Read API
# --------------------------------------------------------------------------- #
async def list_my(
    db: AsyncSession, user_id: int, params: NotificationListParams
) -> tuple[list[NotificationRead], int]:
    where = [Notification.recipient_id == user_id]
    if params.unread_only:
        where.append(Notification.read_at.is_(None))

    total = (
        await db.execute(
            select(func.count(Notification.id)).where(*where)
        )
    ).scalar_one()

    rows = (
        await db.execute(
            select(Notification)
            .where(*where)
            .order_by(Notification.created_at.desc())
            .limit(params.limit)
            .offset(params.offset)
        )
    ).scalars().all()
    return [NotificationRead.model_validate(r) for r in rows], int(total)


async def unread_count(db: AsyncSession, user_id: int) -> UnreadCount:
    count = (
        await db.execute(
            select(func.count(Notification.id)).where(
                Notification.recipient_id == user_id, Notification.read_at.is_(None)
            )
        )
    ).scalar_one()
    return UnreadCount(unread=int(count))


async def mark_read(db: AsyncSession, user_id: int, notification_id: int) -> None:
    row = await db.get(Notification, notification_id)
    if row is None or row.recipient_id != user_id or row.read_at is not None:
        return
    row.read_at = datetime.now(tz=UTC)
    await db.commit()


async def mark_all_read(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.recipient_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(tz=UTC))
    )
    await db.commit()


# --------------------------------------------------------------------------- #
# Create + deliver (called from other domains)
# --------------------------------------------------------------------------- #
async def create_and_deliver(
    db: AsyncSession,
    redis: aioredis.Redis,
    push: PushService,
    *,
    recipient_id: int,
    type: str,
    title: str,
    body: str | None = None,
    data: dict[str, Any] | None = None,
    sender_id: int | None = None,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> NotificationRead:
    """
    Persist a notification + deliver it over the realtime channels.

    Caller is responsible for `await db.commit()` if they want this notification
    to share their existing transaction. We `flush()` here so the id/created_at
    are populated, then leave commit to the caller for batched workflows.
    For one-off uses, this function commits.
    """
    row = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=type,
        title=title,
        body=body,
        data=data or {},
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(row)
    await db.flush()
    await db.commit()

    payload = NotificationRead.model_validate(row).model_dump(mode="json")

    # 1) Live (WebSocket) — also fan out to other workers via Redis Pub/Sub.
    await publish_user(redis, recipient_id, {"type": "notification.new", "data": payload})

    # 2) Push — only if the user isn't online on THIS worker. The pub/sub
    # bridge will reach them on any other worker; only fall back to push if
    # nobody has them connected anywhere. We approximate that with the local
    # manager — good enough for a diploma project.
    if not manager.is_online(recipient_id):
        tokens = (
            await db.execute(
                select(PushToken.token).where(
                    PushToken.user_id == recipient_id, PushToken.is_active.is_(True)
                )
            )
        ).scalars().all()
        if tokens:
            await push.send(
                PushMessage(
                    to=list(tokens),
                    title=title,
                    body=body or "",
                    data={"notification_id": row.id, **(data or {})},
                )
            )

    return NotificationRead.model_validate(row)
