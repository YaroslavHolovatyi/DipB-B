"""
Bars router.

    GET    /bars                          list+search+filter+near-me
    GET    /bars/favorites                my favorites
    GET    /bars/{id}                     detail
    POST   /bars/{id}/favorite            heart
    DELETE /bars/{id}/favorite            unheart
    PUT    /bars/{id}/review              create/update my review (UPSERT)
    DELETE /bars/{id}/review              delete my review
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.bars import service
from app.bars.schemas import (
    BarDetail,
    BarListParams,
    BarReviewCreate,
    BarReviewRead,
    BarSummary,
)
from app.core.deps import CurrentUser, DbSession, get_current_user_optional
from app.shared.pagination import Page

router = APIRouter(prefix="/bars", tags=["bars"])


@router.get("", response_model=Page[BarSummary])
async def list_bars(
    db: DbSession,
    viewer: Annotated[CurrentUser | None, Depends(get_current_user_optional)],
    params: Annotated[BarListParams, Depends()],
) -> Page[BarSummary]:
    """Paginated, filterable bar catalog."""
    items, total = await service.list_bars(db, params, viewer_id=viewer.id if viewer else None)
    return Page[BarSummary](
        items=items, total=total, limit=params.limit, offset=params.offset
    )


@router.get("/favorites", response_model=list[BarSummary])
async def my_favorites(db: DbSession, user: CurrentUser) -> list[BarSummary]:
    return await service.list_my_favorites(db, user.id)


@router.get("/{bar_id}", response_model=BarDetail)
async def get_bar(
    bar_id: int,
    db: DbSession,
    viewer: Annotated[CurrentUser | None, Depends(get_current_user_optional)],
) -> BarDetail:
    return await service.get_bar_detail(db, bar_id, viewer_id=viewer.id if viewer else None)


@router.post(
    "/{bar_id}/favorite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark a bar as a favorite",
)
async def favorite(bar_id: int, db: DbSession, user: CurrentUser) -> None:
    await service.add_favorite(db, user.id, bar_id)


@router.delete(
    "/{bar_id}/favorite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a bar from favorites",
)
async def unfavorite(bar_id: int, db: DbSession, user: CurrentUser) -> None:
    await service.remove_favorite(db, user.id, bar_id)


@router.put("/{bar_id}/review", response_model=BarReviewRead)
async def upsert_review(
    bar_id: int, payload: BarReviewCreate, db: DbSession, user: CurrentUser
) -> BarReviewRead:
    return await service.upsert_review(
        db, user.id, bar_id, rating=payload.rating, text=payload.text
    )


@router.delete("/{bar_id}/review", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(bar_id: int, db: DbSession, user: CurrentUser) -> None:
    await service.delete_review(db, user.id, bar_id)
