"""Pydantic schemas for parties."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PartyStatus = Literal["open", "closed", "cancelled"]
PartyVisibility = Literal["open", "friends_only"]
PartyMemberStatus = Literal["joined", "left", "invited"]
DrinkType = Literal["beer", "cocktail", "wine", "spirit", "non_alcoholic", "other"]


class PartyMemberRead(BaseModel):
    user_id: int
    username: str
    first_name: str
    avatar_url: str | None = None
    status: PartyMemberStatus
    joined_at: datetime


class PartyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    title: str
    description: str | None = None
    max_members: int | None = None
    visibility: PartyVisibility = "open"
    status: PartyStatus
    interest_ids: list[int] = Field(default_factory=list)
    drink_types: list[DrinkType] = Field(default_factory=list)
    member_count: int = 0
    # How many of the party's interests overlap the viewer's — used to sort
    # discovery results (higher = better match). 0 for the viewer's own list.
    match_score: int = 0
    # How many of the party's drink types match the viewer's race-derived
    # taste — a secondary "matches your taste" signal (soft ranking only).
    drink_match: int = 0
    my_membership: PartyMemberStatus | None = None
    is_full: bool = False
    created_at: datetime


class PartyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    max_members: int | None = Field(default=None, ge=2, le=100)
    visibility: PartyVisibility = "open"
    interest_ids: list[int] = Field(default_factory=list, max_length=20)
    drink_types: list[DrinkType] = Field(default_factory=list, max_length=6)
    invite_user_ids: list[int] = Field(default_factory=list)


class PartyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    max_members: int | None = Field(default=None, ge=2, le=100)
    visibility: PartyVisibility | None = None
    status: PartyStatus | None = None
    interest_ids: list[int] | None = Field(default=None, max_length=20)
    drink_types: list[DrinkType] | None = Field(default=None, max_length=6)


class PartyListParams(BaseModel):
    """Filter & paginate `GET /parties`."""

    scope: Literal["mine", "all"] = "all"
    status: PartyStatus | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PartyInvite(BaseModel):
    user_ids: list[int] = Field(min_length=1)
