"""Pydantic schemas for notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_id: int
    sender_id: int | None = None
    type: str
    title: str
    body: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    related_entity_type: str | None = None
    related_entity_id: int | None = None
    read_at: datetime | None = None
    created_at: datetime


class NotificationListParams(BaseModel):
    unread_only: bool = False
    limit: int = Field(default=30, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class UnreadCount(BaseModel):
    unread: int
