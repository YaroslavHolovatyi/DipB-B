"""
Users router — profile self-service, avatar presign, push-token management.

    GET    /users/me
    PATCH  /users/me
    GET    /users/me/stats
    GET    /users/me/interests
    PUT    /users/me/interests
    POST   /users/me/avatar-upload     (returns presigned PUT URL)
    GET    /users/me/push-tokens
    POST   /users/me/push-tokens
    DELETE /users/me/push-tokens/{id}
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select

from app.auth.schemas import UserPublic
from app.core.deps import CurrentUser, DbSession
from app.reference.schemas import InterestRead
from app.services.registry import get_storage_service
from app.services.storage import StorageService
from app.shared.exceptions import BadRequestError, NotFoundError
from app.users.models import Interest, PushToken, UserInterest
from app.users.schemas import (
    AvatarUploadRequest,
    AvatarUploadResponse,
    MyInterestsUpdate,
    PushTokenRead,
    PushTokenRegister,
    UserStats,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic)
async def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession) -> UserPublic:
    """Apply a partial update to the authenticated user."""
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserPublic.model_validate(user)


def _rating_tier(rating: int) -> str:
    """Band the 0–1000 social rating for display. Default start is 100."""
    if rating >= 150:
        return "Legendary"
    if rating >= 110:
        return "Trusted"
    if rating >= 80:
        return "Reliable"
    if rating >= 40:
        return "Shaky"
    return "Unreliable"


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(user: CurrentUser) -> UserStats:
    """Social rating + lifetime attendance counters, plus derived reliability."""
    attended = user.events_attended or 0
    ditched = user.events_ditched or 0
    total = attended + ditched
    reliability = round(100 * attended / total) if total else None
    return UserStats(
        social_rating=user.social_rating,
        events_attended=attended,
        events_ditched=ditched,
        events_total=total,
        reliability_pct=reliability,
        rating_tier=_rating_tier(user.social_rating),
    )


@router.get("/me/interests", response_model=list[InterestRead])
async def get_my_interests(user: CurrentUser, db: DbSession) -> list[InterestRead]:
    rows = (
        await db.execute(
            select(Interest)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user.id)
            .order_by(Interest.label)
        )
    ).scalars().all()
    return [InterestRead.model_validate(r) for r in rows]


@router.put("/me/interests", response_model=list[InterestRead])
async def set_my_interests(
    payload: MyInterestsUpdate, user: CurrentUser, db: DbSession
) -> list[InterestRead]:
    """Replace the user's interest selection with the given ids."""
    wanted = list(dict.fromkeys(payload.interest_ids))  # de-dupe, keep order

    if wanted:
        valid = set(
            (
                await db.execute(
                    select(Interest.id).where(Interest.id.in_(wanted))
                )
            ).scalars().all()
        )
        unknown = [i for i in wanted if i not in valid]
        if unknown:
            raise BadRequestError(f"unknown interest ids: {unknown}")

    # Replace wholesale: clear then re-insert.
    await db.execute(delete(UserInterest).where(UserInterest.user_id == user.id))
    for interest_id in wanted:
        db.add(UserInterest(user_id=user.id, interest_id=interest_id))
    await db.commit()

    rows = (
        await db.execute(
            select(Interest)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user.id)
            .order_by(Interest.label)
        )
    ).scalars().all()
    return [InterestRead.model_validate(r) for r in rows]


@router.post("/me/avatar-upload", response_model=AvatarUploadResponse)
async def avatar_upload(
    payload: AvatarUploadRequest,
    user: CurrentUser,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> AvatarUploadResponse:
    """Hand back a presigned PUT URL the phone can upload directly to."""
    presigned = await storage.presign_upload(
        prefix=f"avatars/{user.id}", content_type=payload.content_type
    )
    return AvatarUploadResponse(
        upload_url=presigned.upload_url,
        public_url=presigned.public_url,
        key=presigned.key,
        expires_in=presigned.expires_in,
    )


@router.get("/me/push-tokens", response_model=list[PushTokenRead])
async def list_push_tokens(user: CurrentUser, db: DbSession) -> list[PushTokenRead]:
    rows = (
        await db.execute(
            select(PushToken)
            .where(PushToken.user_id == user.id, PushToken.is_active.is_(True))
            .order_by(PushToken.created_at.desc())
        )
    ).scalars().all()
    return [PushTokenRead.model_validate(r) for r in rows]


@router.post(
    "/me/push-tokens",
    response_model=PushTokenRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_push_token(
    payload: PushTokenRegister, user: CurrentUser, db: DbSession
) -> PushTokenRead:
    """Idempotently register a device for push. Repeat calls keep the token active."""
    # If the token already exists, reactivate / rebind it to this user.
    existing = (
        await db.execute(select(PushToken).where(PushToken.token == payload.token))
    ).scalar_one_or_none()
    if existing is not None:
        existing.user_id = user.id
        existing.platform = payload.platform
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return PushTokenRead.model_validate(existing)

    row = PushToken(user_id=user.id, token=payload.token, platform=payload.platform)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return PushTokenRead.model_validate(row)


@router.delete(
    "/me/push-tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_push_token(token_id: int, user: CurrentUser, db: DbSession) -> None:
    row = await db.get(PushToken, token_id)
    if row is None or row.user_id != user.id:
        raise NotFoundError("push token not found")
    row.is_active = False
    await db.commit()
