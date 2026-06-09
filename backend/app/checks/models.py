"""
ORM for checks (receipts), split-room participants, item assignments,
dice proposals + votes, and the kind_soul leaderboard event.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import enums
from app.core.db import Base


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bar_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("bars.id", ondelete="SET NULL")
    )
    # Event this receipt came from (WP5). At most one is set; both null for a
    # standalone scan. ON DELETE SET NULL keeps the split if the event is gone.
    raid_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("raids.id", ondelete="SET NULL")
    )
    party_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("parties.id", ondelete="SET NULL")
    )
    bar_name_freeform: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="UAH")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    ocr_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["CheckItem"]] = relationship(
        back_populates="check", cascade="all, delete-orphan", order_by="CheckItem.position"
    )
    participants: Mapped[list["CheckParticipant"]] = relationship(
        back_populates="check", cascade="all, delete-orphan"
    )


class CheckItem(Base):
    __tablename__ = "check_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    check_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checks.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="1")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    check: Mapped[Check] = relationship(back_populates="items")
    assignments: Mapped[list["CheckItemAssignment"]] = relationship(
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0"),
        CheckConstraint("unit_price >= 0"),
        CheckConstraint("total_price >= 0"),
    )


class CheckParticipant(Base):
    __tablename__ = "check_participants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    check_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checks.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))
    # `check_participant_status` enum: invited/joined/ready/left
    status: Mapped[str] = mapped_column(
        enums.check_participant_status, nullable=False, server_default="invited"
    )
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    check: Mapped[Check] = relationship(back_populates="participants")
    assignments: Mapped[list["CheckItemAssignment"]] = relationship(
        cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("check_id", "display_name"),)


class CheckItemAssignment(Base):
    __tablename__ = "check_item_assignments"

    check_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("check_items.id", ondelete="CASCADE"), primary_key=True
    )
    participant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("check_participants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="1")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0"),
        CheckConstraint("amount >= 0"),
    )


class DiceProposal(Base):
    __tablename__ = "dice_proposals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    check_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checks.id", ondelete="CASCADE"), nullable=False
    )
    proposed_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # `dice_proposal_status` enum: pending/accepted/declined/completed/cancelled
    status: Mapped[str] = mapped_column(
        enums.dice_proposal_status, nullable=False, server_default="pending"
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DiceProposalVote(Base):
    __tablename__ = "dice_proposal_votes"

    proposal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dice_proposals.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # `dice_vote` enum: pending/accept/decline
    vote: Mapped[str] = mapped_column(
        enums.dice_vote, nullable=False, server_default="pending"
    )
    voted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KindSoulEvent(Base):
    __tablename__ = "kind_soul_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    check_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checks.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    proposal_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("dice_proposals.id", ondelete="SET NULL")
    )
    payer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    payer_participant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("check_participants.id", ondelete="SET NULL")
    )
    total_paid_for_others: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # `check_payment_method` enum
    decided_via: Mapped[str] = mapped_column(
        enums.check_payment_method, nullable=False, server_default="d20_dice"
    )
    event_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
