"""Pydantic schemas for raids."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


RaidStatus = Literal["planned", "ongoing", "completed", "cancelled", "aborted"]
# Full RSVP/attendance lifecycle: going → arrived → attended | no_show.
RsvpStatus = Literal[
    "going", "maybe", "declined", "arrived", "attended", "no_show"
]
# What an RSVP'ing user may set themselves (lifecycle states are set by the
# check-in/verification endpoints, not by the user picking from a list).
RsvpChoice = Literal["going", "maybe", "declined"]
RaidVisibility = Literal["open", "friends_only"]
# Final per-participant verdict the host assigns at verification time.
AttendanceVerdict = Literal["attended", "no_show"]
DrinkType = Literal["beer", "cocktail", "wine", "spirit", "non_alcoholic", "other"]


class RaidParticipantRead(BaseModel):
    user_id: int
    status: RsvpStatus
    joined_at: datetime
    arrived_at: datetime | None = None
    verified_at: datetime | None = None


class RaidParticipantDetail(BaseModel):
    """Roster row for the host's verification screen — includes display info."""

    user_id: int
    username: str
    first_name: str
    avatar_url: str | None = None
    status: RsvpStatus
    arrived_at: datetime | None = None
    verified_at: datetime | None = None


class RaidRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    bar_id: int | None = None
    organizer_id: int
    scheduled_at: datetime
    ends_at: datetime | None = None
    max_participants: int | None = None
    theme: str | None = None
    status: RaidStatus
    visibility: RaidVisibility = "open"
    cover_image_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_m: float | None = None
    participant_count: int = 0
    drink_types: list[DrinkType] = Field(default_factory=list)
    # How many of the raid's drink types match the viewer's race-derived taste
    # — a secondary "matches your taste" signal (soft ranking only).
    drink_match: int = 0
    my_rsvp: RsvpStatus | None = None


class RaidCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    bar_id: int | None = Field(default=None, ge=1)
    scheduled_at: datetime
    ends_at: datetime | None = None
    max_participants: int | None = Field(default=None, ge=2, le=200)
    theme: str | None = Field(default=None, max_length=120)
    visibility: RaidVisibility = "open"
    cover_image_url: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    drink_types: list[DrinkType] = Field(default_factory=list, max_length=6)
    invite_user_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_location(self) -> "RaidCreate":
        # If bar_id is null, we need explicit lat/lon for "near me" to work.
        if self.bar_id is None and (self.latitude is None or self.longitude is None):
            # Allow no location at all (freeform location with no map pin).
            return self
        return self


class RaidUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    scheduled_at: datetime | None = None
    ends_at: datetime | None = None
    max_participants: int | None = Field(default=None, ge=2, le=200)
    theme: str | None = Field(default=None, max_length=120)
    visibility: RaidVisibility | None = None
    cover_image_url: str | None = None
    status: RaidStatus | None = None
    drink_types: list[DrinkType] | None = Field(default=None, max_length=6)


class RaidRsvp(BaseModel):
    status: RsvpChoice


class AttendanceMark(BaseModel):
    """One host verdict row for POST /{raid_id}/verify."""

    user_id: int
    verdict: AttendanceVerdict


class RaidVerify(BaseModel):
    """Host confirms who actually showed up. Any going/arrived participant
    not listed is left untouched (the host can verify in several passes)."""

    marks: list[AttendanceMark] = Field(min_length=1)


class RaidListParams(BaseModel):
    """Filter & paginate `GET /raids`."""

    scope: Literal["mine", "all"] = "mine"
    status: RaidStatus | None = None
    near_lat: float | None = Field(default=None, ge=-90, le=90)
    near_lon: float | None = Field(default=None, ge=-180, le=180)
    radius_m: int | None = Field(default=None, ge=100, le=50_000)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
