"""
Reference-data router.

Read-only endpoints for the static lookup tables. These are fronted by a
short-TTL cache in production; for now they're plain selects.

    GET /reference/cities
    GET /reference/vibes
    GET /reference/drinks
    GET /reference/races
    GET /reference/races/{race_id}
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DbSession
from app.reference.models import City, Drink, Race, Vibe
from app.reference.schemas import (
    CityRead,
    DrinkRead,
    InterestRead,
    RaceRead,
    VibeRead,
)
from app.shared.exceptions import NotFoundError
from app.users.models import Interest

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/cities", response_model=list[CityRead])
async def list_cities(db: DbSession) -> list[CityRead]:
    rows = (await db.execute(select(City).order_by(City.name))).scalars().all()
    return [CityRead.model_validate(r) for r in rows]


@router.get("/vibes", response_model=list[VibeRead])
async def list_vibes(db: DbSession) -> list[VibeRead]:
    rows = (await db.execute(select(Vibe).order_by(Vibe.name))).scalars().all()
    return [VibeRead.model_validate(r) for r in rows]


@router.get("/drinks", response_model=list[DrinkRead])
async def list_drinks(db: DbSession) -> list[DrinkRead]:
    rows = (await db.execute(select(Drink).order_by(Drink.name))).scalars().all()
    return [DrinkRead.model_validate(r) for r in rows]


@router.get("/interests", response_model=list[InterestRead])
async def list_interests(db: DbSession) -> list[InterestRead]:
    rows = (await db.execute(select(Interest).order_by(Interest.label))).scalars().all()
    return [InterestRead.model_validate(r) for r in rows]


@router.get("/races", response_model=list[RaceRead])
async def list_races(db: DbSession) -> list[RaceRead]:
    rows = (await db.execute(select(Race).order_by(Race.name))).scalars().all()
    return [RaceRead.model_validate(r) for r in rows]


@router.get("/races/{race_id}", response_model=RaceRead)
async def get_race(race_id: int, db: DbSession) -> RaceRead:
    row = await db.get(Race, race_id)
    if row is None:
        raise NotFoundError("race not found")
    return RaceRead.model_validate(row)
