"""Notifications router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbSession
from app.notifications import service
from app.notifications.schemas import (
    NotificationListParams,
    NotificationRead,
    UnreadCount,
)
from app.shared.pagination import Page

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationRead])
async def list_notifications(
    db: DbSession,
    user: CurrentUser,
    params: Annotated[NotificationListParams, Depends()],
) -> Page[NotificationRead]:
    items, total = await service.list_my(db, user.id, params)
    return Page[NotificationRead](
        items=items, total=total, limit=params.limit, offset=params.offset
    )


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(db: DbSession, user: CurrentUser) -> UnreadCount:
    return await service.unread_count(db, user.id)


@router.post(
    "/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT
)
async def mark_read(notification_id: int, db: DbSession, user: CurrentUser) -> None:
    await service.mark_read(db, user.id, notification_id)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(db: DbSession, user: CurrentUser) -> None:
    await service.mark_all_read(db, user.id)
