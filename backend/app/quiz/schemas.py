"""Pydantic schemas for the quiz."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuizAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: int


class QuizQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    text: str
    image_url: str | None = None
    answers: list[QuizAnswerRead]


class QuizSubmission(BaseModel):
    """One pick per question. The client sends a flat list of answer ids.

    `gender` comes from the final quiz step and selects the m/f race avatar.
    Optional so older clients that don't send it still submit successfully.
    """

    answer_ids: list[int] = Field(min_length=1)
    gender: Literal["m", "f"] | None = None


class QuizResult(BaseModel):
    race_id: int
    race_slug: str
    race_name: str
    gender: str | None = None
    score_breakdown: dict[int, int]  # race_id -> total
    completed_at: datetime
