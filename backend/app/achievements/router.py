"""Achievements router."""

from __future__ import annotations

from fastapi import APIRouter

from app.achievements import service
from app.achievements.schemas import AchievementRead, UserAchievementRead
from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("", response_model=list[AchievementRead])
async def list_all(db: DbSession) -> list[AchievementRead]:
    return await service.list_all(db)


@router.get("/me", response_model=list[UserAchievementRead])
async def list_mine(db: DbSession, user: CurrentUser) -> list[UserAchievementRead]:
    return await service.list_for_user(db, user.id)


@router.get("/me/points")
async def my_points(db: DbSession, user: CurrentUser) -> dict[str, int]:
    return {"points": await service.points_total(db, user.id)}
