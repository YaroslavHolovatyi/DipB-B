"""Pydantic schemas for the users domain."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserUpdate(BaseModel):
    """Partial-update payload for `PATCH /users/me`."""

    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    avatar_url: str | None = None
    main_city_id: int | None = Field(default=None, ge=1)
    bio: str | None = Field(default=None, max_length=500)


class MyInterestsUpdate(BaseModel):
    """Replace the authenticated user's interest selection."""

    interest_ids: list[int] = Field(default_factory=list, max_length=30)


class UserStats(BaseModel):
    """Social rating + attendance counters for the profile screen.

    `events_total`, `reliability_pct`, and `rating_tier` are derived server-side
    so every client renders the same reputation summary.
    """

    social_rating: int
    events_attended: int
    events_ditched: int
    events_total: int
    # Share of committed events actually attended, 0–100. Null until the user
    # has any verified event either way.
    reliability_pct: int | None = None
    # Human-readable band for the social rating (Unreliable → Legendary).
    rating_tier: str


class AvatarUploadRequest(BaseModel):
    content_type: str = Field(default="image/jpeg")


class AvatarUploadResponse(BaseModel):
    upload_url: str
    public_url: str
    key: str
    expires_in: int


class PushTokenRegister(BaseModel):
    token: str = Field(min_length=8, max_length=512)
    platform: Literal["ios", "android", "web"]


class PushTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    platform: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
