"""Pydantic schemas for Tavern Tales."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


DndMode = Literal["munchkin", "normal", "dungeon_master_pro"]
DndClass = Literal[
    "barbarian", "bard", "cleric", "druid", "fighter", "monk",
    "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
]
DndAlignment = Literal[
    "lawful_good", "neutral_good", "chaotic_good",
    "lawful_neutral", "true_neutral", "chaotic_neutral",
    "lawful_evil", "neutral_evil", "chaotic_evil",
]
SessionStatus = Literal["active", "paused", "completed", "abandoned"]
MessageRole = Literal["user", "assistant", "system", "dice_roll", "narration"]


# --------------------------------------------------------------------------- #
# Class info
# --------------------------------------------------------------------------- #
class DndClassInfoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: DndClass
    name: str
    description: str
    hit_die: int
    primary_ability: str | None = None
    icon_url: str | None = None


# --------------------------------------------------------------------------- #
# Characters
# --------------------------------------------------------------------------- #
class CharacterBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    class_slug: DndClass
    alignment: DndAlignment | None = None
    stats: dict[str, int] = Field(default_factory=dict)
    background: str | None = Field(default=None, max_length=2000)
    avatar_url: str | None = None


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    alignment: DndAlignment | None = None
    stats: dict[str, int] | None = None
    background: str | None = Field(default=None, max_length=2000)
    avatar_url: str | None = None


class CharacterRead(CharacterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    race_id: int
    level: int
    xp: int
    hp_current: int
    hp_max: int
    armor_class: int
    inventory: list[dict[str, Any]] = Field(default_factory=list)
    spells_known: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    last_played_at: datetime | None = None


# --------------------------------------------------------------------------- #
# Sessions + messages
# --------------------------------------------------------------------------- #
class SessionCreate(BaseModel):
    character_id: int
    mode: DndMode
    title: str | None = Field(default=None, max_length=120)


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    mode: DndMode
    title: str | None = None
    summary: str | None = None
    status: SessionStatus
    turn_count: int
    input_tokens_used: int
    output_tokens_used: int
    session_metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    last_message_at: datetime | None = None
    ended_at: datetime | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: MessageRole
    content: str
    message_metadata: dict[str, Any] = Field(default_factory=dict)
    tokens_in: int | None = None
    tokens_out: int | None = None
    created_at: datetime


class UserTurn(BaseModel):
    """Body for `POST /tavern/sessions/{id}/turn`."""

    content: str = Field(min_length=1, max_length=2000)


class TurnResponse(BaseModel):
    """The combined user + assistant turn, returned to the client in one call."""

    user_message: MessageRead
    assistant_message: MessageRead
    session: SessionRead


class DiceRoll(BaseModel):
    """Body for `POST /tavern/sessions/{id}/roll` — record a dice outcome."""

    dice: str = Field(default="d20")
    modifier: int = 0
    result: int = Field(ge=1)
    purpose: str | None = Field(default=None, max_length=80)


# --------------------------------------------------------------------------- #
# Quota
# --------------------------------------------------------------------------- #
class QuotaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    daily_tokens_used: int
    daily_tokens_limit: int
    daily_reset_at: date
    monthly_tokens_used: int
    monthly_tokens_limit: int
    monthly_reset_at: date
