"""Raids ORM (events / planned gatherings)."""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import enums
from app.core.db import Base


class Raid(Base):
    __tablename__ = "raids"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    bar_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("bars.id", ondelete="SET NULL")
    )
    organizer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326)
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_participants: Mapped[int | None] = mapped_column(Integer)
    theme: Mapped[str | None] = mapped_column(Text)
    # `raid_status` enum on DB: planned|ongoing|completed|cancelled|aborted
    status: Mapped[str] = mapped_column(
        enums.raid_status, nullable=False, server_default="planned"
    )
    # `raid_visibility` enum on DB: open|friends_only
    visibility: Mapped[str] = mapped_column(
        enums.raid_visibility, nullable=False, server_default="open"
    )
    cover_image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    participants: Mapped[list["RaidParticipant"]] = relationship(
        cascade="all, delete-orphan"
    )
    drinks: Mapped[list["RaidDrink"]] = relationship(
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("max_participants IS NULL OR max_participants > 0"),
    )


class RaidDrink(Base):
    """Which drink types this raid is about — tags for soft taste-matching."""

    __tablename__ = "raid_drinks"

    raid_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("raids.id", ondelete="CASCADE"), primary_key=True
    )
    # `drink_type` enum on DB: beer|cocktail|wine|spirit|non_alcoholic|other
    drink_type: Mapped[str] = mapped_column(enums.drink_type, primary_key=True)


class RaidParticipant(Base):
    __tablename__ = "raid_participants"

    raid_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("raids.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # `raid_rsvp_status` enum on DB:
    # going|maybe|declined|arrived|attended|no_show
    status: Mapped[str] = mapped_column(
        enums.raid_rsvp_status, nullable=False, server_default="going"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
