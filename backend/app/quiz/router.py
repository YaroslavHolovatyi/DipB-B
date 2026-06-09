"""Quiz router."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.quiz import service
from app.quiz.schemas import QuizQuestionRead, QuizResult, QuizSubmission
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/questions", response_model=list[QuizQuestionRead])
async def list_questions(db: DbSession) -> list[QuizQuestionRead]:
    return await service.list_questions(db)


@router.post("/submit", response_model=QuizResult)
async def submit_quiz(
    payload: QuizSubmission, db: DbSession, user: CurrentUser
) -> QuizResult:
    return await service.submit_quiz(db, user, payload)


@router.get("/me", response_model=QuizResult)
async def get_my_latest(db: DbSession, user: CurrentUser) -> QuizResult:
    row = await service.latest_result(db, user.id)
    if row is None:
        raise NotFoundError("no quiz result yet — take the quiz first")
    return row
