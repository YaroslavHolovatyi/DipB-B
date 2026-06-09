"""Achievement schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    category: str
    race_id: int | None = None
    icon_url: str | None = None
    points: int
    requirement: dict[str, Any] = Field(default_factory=dict)


class UserAchievementRead(BaseModel):
    achievement: AchievementRead
    awarded_at: datetime
    progress: dict[str, Any] = Field(default_factory=dict)
