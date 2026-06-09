"""Pydantic schemas for reference-data endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    country_code: str
    timezone: str


class VibeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str | None = None
    icon_url: str | None = None


class DrinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    type: str
    description: str | None = None
    image_url: str | None = None


class RaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    title: str | None = None
    description: str
    icon_url: str | None = None
    primary_color: str | None = None


class InterestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
