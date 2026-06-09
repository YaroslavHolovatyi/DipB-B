"""
ORM models for the static reference tables: cities, vibes, drinks, races,
and the race↔drinks / race↔vibes affinity tables.
"""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import enums
from app.core.db import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default="UA")
    timezone: Mapped[str] = mapped_column(Text, nullable=False, server_default="Europe/Kyiv")
    location: Mapped[str | None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Vibe(Base):
    __tablename__ = "vibes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon_url: Mapped[str | None] = mapped_column(Text)


class Drink(Base):
    __tablename__ = "drinks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # `drink_type` enum on the DB; the ORM treats it as a plain string and lets
    # PG enforce the legal values.
    type: Mapped[str] = mapped_column(
        enums.drink_type, nullable=False, server_default="other"
    )
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)


class Race(Base):
    __tablename__ = "races"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(String(7))

    drinks: Mapped[list["RaceDrink"]] = relationship(cascade="all, delete-orphan")
    vibes: Mapped[list["RaceVibe"]] = relationship(cascade="all, delete-orphan")


class RaceDrink(Base):
    __tablename__ = "race_drinks"

    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="CASCADE"), primary_key=True
    )
    drink_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("drinks.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")

    __table_args__ = (CheckConstraint("weight BETWEEN 1 AND 10"),)


class RaceVibe(Base):
    __tablename__ = "race_vibes"

    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="CASCADE"), primary_key=True
    )
    vibe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vibes.id", ondelete="CASCADE"), primary_key=True
    )
