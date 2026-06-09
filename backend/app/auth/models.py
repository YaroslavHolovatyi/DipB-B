"""
ORM models needed for authentication.

Only the columns the auth flow actually touches are mapped here. The rest of
the `users` columns (avatar, race, achievements counts, …) will be mapped in
their respective domain modules as they are wired up.

Why partial mapping? SQLAlchemy is happy to map a subset of columns, the table
already exists from the schema baseline, and this keeps each domain owning
just the slice of the schema it cares about.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import CITEXT, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import enums
from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str | None] = mapped_column(Text)

    username: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    avatar_url: Mapped[str | None] = mapped_column(Text)

    # Profile foundation (WP1). `bio` + interests power party matching;
    # `social_rating` and the event counters power the rating/stats layer.
    bio: Mapped[str | None] = mapped_column(Text)
    social_rating: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="100"
    )
    events_attended: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    events_ditched: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    main_city_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False
    )
    race_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="SET NULL")
    )

    # `user_role` enum on the DB side — we accept it as a string in ORM and let
    # the DB enforce the values. Mapping the enum properly is deferred until we
    # need it in Python logic.
    role: Mapped[str] = mapped_column(enums.user_role, nullable=False, server_default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # Mirror the DB's `DEFAULT now()` on these so SQLAlchemy emits an INSERT
    # that lets Postgres fill them in (and reads the value back via RETURNING).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user", "user_id"),
        Index(
            "idx_refresh_tokens_active",
            "user_id",
            postgresql_where="revoked_at IS NULL",
        ),
    )
