"""Tavern Tales (D&D AI Dungeon Master) ORM."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import enums
from app.core.db import Base


class DndClassInfo(Base):
    """Seeded reference table — the twelve 5e classes."""

    __tablename__ = "dnd_class_info"

    # PK is the `dnd_class` enum.
    slug: Mapped[str] = mapped_column(enums.dnd_class, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hit_die: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    primary_ability: Mapped[str | None] = mapped_column(Text)
    icon_url: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (CheckConstraint("hit_die IN (6, 8, 10, 12)"),)


class DndCharacter(Base):
    __tablename__ = "dnd_characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="RESTRICT"), nullable=False
    )
    class_slug: Mapped[str] = mapped_column(
        enums.dnd_class, ForeignKey("dnd_class_info.slug"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # `dnd_alignment` enum (nullable)
    alignment: Mapped[str | None] = mapped_column(enums.dnd_alignment)

    stats: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    hp_current: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    hp_max: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    armor_class: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="10")

    background: Mapped[str | None] = mapped_column(Text)
    inventory: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    spells_known: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    avatar_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list["DndSession"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 20"),
        CheckConstraint("xp >= 0"),
    )


class DndSession(Base):
    __tablename__ = "dnd_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    character_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dnd_characters.id", ondelete="CASCADE"), nullable=False
    )
    # `dnd_mode` enum
    mode: Mapped[str] = mapped_column(enums.dnd_mode, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    # `dnd_session_status` enum
    status: Mapped[str] = mapped_column(
        enums.dnd_session_status, nullable=False, server_default="active"
    )
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    input_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    output_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    session_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    messages: Mapped[list["DndMessage"]] = relationship(
        cascade="all, delete-orphan", order_by="DndMessage.created_at"
    )


class DndMessage(Base):
    __tablename__ = "dnd_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dnd_sessions.id", ondelete="CASCADE"), nullable=False
    )
    # `dnd_message_role` enum: user / assistant / system / dice_roll / narration
    role: Mapped[str] = mapped_column(enums.dnd_message_role, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DndUsageQuota(Base):
    __tablename__ = "dnd_usage_quota"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    daily_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    daily_tokens_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30000")
    daily_reset_at: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    monthly_tokens_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default="500000")
    monthly_reset_at: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
