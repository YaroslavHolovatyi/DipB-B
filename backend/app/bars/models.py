"""
ORM models for the bars catalog.

Note on PostGIS: the `bars.location` column is a `GEOGRAPHY(POINT, 4326)`.
We map it via GeoAlchemy2 — when we need lat/lon for output we run a small
ST_X / ST_Y projection in the query (see `app.bars.service.select_bar_row`),
keeping the model itself untyped about the projection format.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Bar(Base):
    __tablename__ = "bars"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    city_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False
    )
    address: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326)
    )
    description: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    # `price_category` is a native Postgres ENUM. It MUST be mapped to that
    # enum type (not String), otherwise comparisons/inserts bind the value as
    # VARCHAR and Postgres errors with "operator does not exist:
    # price_category = character varying". create_type=False — the type already
    # exists (created in schema.sql), so SQLAlchemy must not try to recreate it.
    price_category: Mapped[str] = mapped_column(
        PGEnum(
            "budget",
            "mid",
            "premium",
            "luxury",
            name="price_category",
            create_type=False,
        ),
        nullable=False,
        server_default="mid",
    )

    rating_avg: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, server_default="0.00")
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    work_hours: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    # `search_vector` (tsvector) and the trigger that maintains it live in the
    # schema — we don't touch them from ORM.

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BarVibe(Base):
    __tablename__ = "bar_vibes"

    bar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bars.id", ondelete="CASCADE"), primary_key=True
    )
    vibe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vibes.id", ondelete="CASCADE"), primary_key=True
    )


class BarPhoto(Base):
    __tablename__ = "bar_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bars.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BarReview(Base):
    __tablename__ = "bar_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bars.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("bar_id", "user_id", name="bar_reviews_bar_id_user_id_key"),)


class BarFavorite(Base):
    __tablename__ = "bar_favorites"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    bar_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bars.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
