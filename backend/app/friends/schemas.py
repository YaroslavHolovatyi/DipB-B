"""Pydantic schemas for the friends + friend-groups endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Friend listings
# --------------------------------------------------------------------------- #
class FriendUser(BaseModel):
    """Trimmed-down user info attached to a friend / member row."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str
    avatar_url: str | None = None
    race_id: int | None = None


class FriendRead(BaseModel):
    user: FriendUser
    nickname: str | None = None
    is_muted: bool
    accepted_at: datetime | None = None


# --------------------------------------------------------------------------- #
# Friend requests
# --------------------------------------------------------------------------- #
class FriendRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    recipient_id: int
    message: str | None = None
    status: Literal["pending", "accepted", "declined", "cancelled"]
    created_at: datetime
    responded_at: datetime | None = None


class FriendRequestCreate(BaseModel):
    recipient_id: int = Field(ge=1)
    message: str | None = Field(default=None, max_length=300)


# --------------------------------------------------------------------------- #
# Friend groups ("Party for Dungeon")
# --------------------------------------------------------------------------- #
class FriendGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    slug: str | None = None
    description: str | None = None
    image_url: str | None = None
    member_count: int = 0


class FriendGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = None
    initial_member_ids: list[int] = Field(default_factory=list)


class FriendGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = None


class FriendGroupMemberRead(BaseModel):
    user: FriendUser
    role: Literal["member", "admin"]
    joined_at: datetime
