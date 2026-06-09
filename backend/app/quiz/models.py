"""Quiz ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    position: Mapped[int] = mapped_column(SmallInteger, unique=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    answers: Mapped[list["QuizAnswer"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuizAnswer.position",
    )


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    question: Mapped[QuizQuestion] = relationship(back_populates="answers")
    races: Mapped[list["QuizAnswerRace"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("question_id", "position"),)


class QuizAnswerRace(Base):
    __tablename__ = "quiz_answer_races"

    answer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("quiz_answers.id", ondelete="CASCADE"), primary_key=True
    )
    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="CASCADE"), primary_key=True
    )
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")


class UserQuizResult(Base):
    __tablename__ = "user_quiz_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="RESTRICT"), nullable=False
    )
    score_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
