"""
Quiz service.

The submission flow:

    1. Validate the answer ids actually exist.
    2. Sum `quiz_answer_races.score` grouped by race.
    3. Pick the winning race (max score; deterministic tiebreaker = race id ASC).
    4. Persist a `user_quiz_results` row and set `users.race_id`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.quiz.models import (
    QuizAnswer,
    QuizAnswerRace,
    QuizQuestion,
    UserQuizResult,
)
from app.quiz.schemas import QuizQuestionRead, QuizResult, QuizSubmission
from app.reference.models import Race
from app.shared.exceptions import BadRequestError


async def list_questions(db: AsyncSession) -> list[QuizQuestionRead]:
    """Active questions with their answers, in display order."""
    # `selectinload` eager-loads the answers in a second query; async
    # SQLAlchemy can't lazy-load relationships on attribute access, so the
    # eager option is required or `q.answers` raises MissingGreenlet.
    questions = (
        (
            await db.execute(
                select(QuizQuestion)
                .where(QuizQuestion.is_active.is_(True))
                .options(selectinload(QuizQuestion.answers))
                .order_by(QuizQuestion.position)
            )
        )
        .scalars()
        .all()
    )

    return [QuizQuestionRead.model_validate(q) for q in questions]


async def submit_quiz(
    db: AsyncSession, user: User, payload: QuizSubmission
) -> QuizResult:
    """Score the submission, pick a race, persist."""
    if not payload.answer_ids:
        raise BadRequestError("at least one answer required")

    # 1) Validate ids
    valid_count = (
        await db.execute(
            select(func.count(QuizAnswer.id)).where(QuizAnswer.id.in_(payload.answer_ids))
        )
    ).scalar_one()
    if int(valid_count) != len(set(payload.answer_ids)):
        raise BadRequestError("one or more answer ids are invalid")

    # 2) Sum score by race
    score_rows = (
        await db.execute(
            select(QuizAnswerRace.race_id, func.sum(QuizAnswerRace.score))
            .where(QuizAnswerRace.answer_id.in_(payload.answer_ids))
            .group_by(QuizAnswerRace.race_id)
        )
    ).all()

    if not score_rows:
        raise BadRequestError("answers do not award race points")

    breakdown: dict[int, int] = {int(rid): int(score or 0) for rid, score in score_rows}

    # 3) Pick winner — max score, tiebreaker = lowest race id
    winning_race_id = sorted(
        breakdown.items(), key=lambda kv: (-kv[1], kv[0])
    )[0][0]

    # 4) Persist
    user.race_id = winning_race_id
    if payload.gender is not None:
        user.gender = payload.gender
    db.add(
        UserQuizResult(
            user_id=user.id,
            race_id=winning_race_id,
            score_breakdown={str(k): v for k, v in breakdown.items()},
            completed_at=datetime.now(tz=UTC),
        )
    )
    await db.flush()

    race = await db.get(Race, winning_race_id)
    assert race is not None  # winner was just chosen from existing race_ids

    await db.commit()

    return QuizResult(
        race_id=race.id,
        race_slug=race.slug,
        race_name=race.name,
        gender=user.gender,
        score_breakdown=breakdown,
        completed_at=datetime.now(tz=UTC),
    )


async def latest_result(db: AsyncSession, user_id: int) -> QuizResult | None:
    row = (
        await db.execute(
            select(UserQuizResult)
            .where(UserQuizResult.user_id == user_id)
            .order_by(UserQuizResult.completed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    race = await db.get(Race, row.race_id)
    if race is None:
        return None
    user = await db.get(User, user_id)
    return QuizResult(
        race_id=race.id,
        race_slug=race.slug,
        race_name=race.name,
        gender=user.gender if user is not None else None,
        score_breakdown={int(k): int(v) for k, v in (row.score_breakdown or {}).items()},
        completed_at=row.completed_at,
    )
