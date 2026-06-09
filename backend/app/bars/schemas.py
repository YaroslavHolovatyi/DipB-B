"""Pydantic schemas for the bars domain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PriceCategory = Literal["budget", "mid", "premium", "luxury"]


# --------------------------------------------------------------------------- #
# Bar reads
# --------------------------------------------------------------------------- #
class BarSummary(BaseModel):
    """Card-style payload used by lists and the recommended-near-you feed."""

    id: int
    slug: str
    name: str
    city_id: int
    address: str | None = None
    image_url: str | None = None
    price_category: PriceCategory
    # float, not Decimal: Pydantic serializes Decimal as a JSON *string*
    # ("4.5"), which breaks the mobile client's `rating_avg.toFixed(1)`.
    # float serializes as a JSON number, matching the TS type `number`.
    rating_avg: float
    rating_count: int
    latitude: float | None = None
    longitude: float | None = None
    distance_m: float | None = None  # set by "near me" queries
    is_favorite: bool = False


class BarPhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    alt_text: str | None = None
    position: int


class BarVibeRead(BaseModel):
    id: int
    slug: str
    name: str


class BarReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    rating: int
    text: str | None = None
    created_at: datetime


class BarDetail(BarSummary):
    description: str | None = None
    phone: str | None = None
    website: str | None = None
    work_hours: dict[str, Any]
    photos: list[BarPhotoRead] = Field(default_factory=list)
    vibes: list[BarVibeRead] = Field(default_factory=list)
    recent_reviews: list[BarReviewRead] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# List filters
# --------------------------------------------------------------------------- #
class BarListParams(BaseModel):
    q: str | None = Field(default=None, description="Free-text search across name+description+address")
    city_id: int | None = None
    price_category: PriceCategory | None = None
    vibe_id: int | None = None
    min_rating: float | None = Field(default=None, ge=0, le=5)
    # Geo
    near_lat: float | None = Field(default=None, ge=-90, le=90)
    near_lon: float | None = Field(default=None, ge=-180, le=180)
    radius_m: int | None = Field(default=None, ge=100, le=50_000)
    # Pagination
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# --------------------------------------------------------------------------- #
# Reviews
# --------------------------------------------------------------------------- #
class BarReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)
