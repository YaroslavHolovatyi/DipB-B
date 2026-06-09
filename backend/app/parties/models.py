"""Parties ORM — interest-matched "looking for party members" gatherings."""

from __future__ import annotations

from datetime import datetime

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


class Party(Base):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    host_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    max_members: Mapped[int | None] = mapped_column(Integer)
    # `party_visibility` enum on DB: open|friends_only
    visibility: Mapped[str] = mapped_column(
        enums.party_visibility, nullable=False, server_default="open"
    )
    # `party_status` enum on DB: open|closed|cancelled
    status: Mapped[str] = mapped_column(
        enums.party_status, nullable=False, server_default="open"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    members: Mapped[list["PartyMember"]] = relationship(
        cascade="all, delete-orphan"
    )
    interests: Mapped[list["PartyInterest"]] = relationship(
        cascade="all, delete-orphan"
    )
    drinks: Mapped[list["PartyDrink"]] = relationship(
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("max_members IS NULL OR max_members > 1"),
    )


class PartyDrink(Base):
    """Which drink types this party is about — tags for soft taste-matching."""

    __tablename__ = "party_drinks"

    party_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True
    )
    # `drink_type` enum on DB: beer|cocktail|wine|spirit|non_alcoholic|other
    drink_type: Mapped[str] = mapped_column(enums.drink_type, primary_key=True)


class PartyInterest(Base):
    __tablename__ = "party_interests"

    party_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True
    )
    interest_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True
    )


class PartyMember(Base):
    __tablename__ = "party_members"

    party_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # `party_member_status` enum on DB: joined|left|invited
    status: Mapped[str] = mapped_column(
        enums.party_member_status, nullable=False, server_default="joined"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
