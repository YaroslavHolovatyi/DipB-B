"""Pydantic schemas for the quiz."""

from __future__ import annotations

from datetime import datetime

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
    """One pick per question. The client sends a flat list of answer ids."""

    answer_ids: list[int] = Field(min_length=1)


class QuizResult(BaseModel):
    race_id: int
    race_slug: str
    race_name: str
    score_breakdown: dict[int, int]  # race_id -> total
    completed_at: datetime
