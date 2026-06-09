"""
Venue search router  —  GET /venues
====================================

A search-focused surface for bar discovery.  All heavy lifting (PostGIS
geo-filter, FTS, vibe/price facets, pagination) is delegated to the
existing ``app.bars.service`` layer; this router is purely an HTTP/schema
boundary.

Endpoints
---------
GET  /venues                  Paginated bar catalog with all search filters.
GET  /venues/search           Alias with the same params as GET /venues —
                              friendlier URL for clients that build a
                              dedicated "Search" screen.
GET  /venues/nearby           Geo-first shorthand: requires lat/lon/radius,
                              returns bars sorted closest-first.
GET  /venues/{venue_id}       Full bar detail (photos, vibes, recent reviews).
GET  /venues/by-slug/{slug}   Resolve a bar by its human-readable slug (useful
                              for deep-links and share URLs).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bars import service as bar_service
from app.bars.models import Bar
from app.bars.schemas import BarDetail, BarListParams, BarSummary
from app.core.deps import DbSession, get_current_user_optional
from app.auth.models import User
from app.shared.pagination import Page

router = APIRouter(prefix="/venues", tags=["venues"])

# Convenience type alias so route signatures stay readable.
OptionalViewer = Annotated[User | None, Depends(get_current_user_optional)]


# --------------------------------------------------------------------------- #
# Paginated catalog / primary search surface
# --------------------------------------------------------------------------- #

@router.get(
    "",
    response_model=Page[BarSummary],
    summary="Search & filter the venue catalog",
    description=(
        "Returns a paginated list of bars.  Supports free-text search (`q`), "
        "geo-proximity filtering (`near_lat`/`near_lon`/`radius_m`), city, "
        "price category, vibe tag, and minimum rating filters.  When a geo "
        "filter is active results are sorted by distance; otherwise by rating."
    ),
)
async def list_venues(
    db: DbSession,
    viewer: OptionalViewer,
    params: Annotated[BarListParams, Depends()],
) -> Page[BarSummary]:
    items, total = await bar_service.list_bars(
        db, params, viewer_id=viewer.id if viewer else None
    )
    return Page[BarSummary](
        items=items, total=total, limit=params.limit, offset=params.offset
    )


@router.get(
    "/search",
    response_model=Page[BarSummary],
    summary="Venue full-text + filter search (alias)",
    description=(
        "Identical to `GET /venues` — exposed as a separate path so mobile "
        "clients can use a dedicated 'Search' URL without changing query logic."
    ),
)
async def search_venues(
    db: DbSession,
    viewer: OptionalViewer,
    params: Annotated[BarListParams, Depends()],
) -> Page[BarSummary]:
    items, total = await bar_service.list_bars(
        db, params, viewer_id=viewer.id if viewer else None
    )
    return Page[BarSummary](
        items=items, total=total, limit=params.limit, offset=params.offset
    )


# --------------------------------------------------------------------------- #
# Geo-first "nearby" shorthand
# --------------------------------------------------------------------------- #

@router.get(
    "/nearby",
    response_model=Page[BarSummary],
    summary="Bars near a coordinate, sorted by distance",
    description=(
        "Geo-first convenience endpoint.  All three geo params are **required** "
        "here (unlike the general catalog where they are optional).  Results are "
        "always sorted closest-first."
    ),
)
async def nearby_venues(
    db: DbSession,
    viewer: OptionalViewer,
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude of the origin point")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Longitude of the origin point")],
    radius_m: Annotated[
        int,
        Query(ge=100, le=50_000, description="Search radius in metres (100 – 50 000)"),
    ] = 2_000,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[BarSummary]:
    params = BarListParams(
        near_lat=lat,
        near_lon=lon,
        radius_m=radius_m,
        limit=limit,
        offset=offset,
    )
    items, total = await bar_service.list_bars(
        db, params, viewer_id=viewer.id if viewer else None
    )
    return Page[BarSummary](
        items=items, total=total, limit=limit, offset=offset
    )


# --------------------------------------------------------------------------- #
# Detail by slug  (must be declared BEFORE /{venue_id} to avoid shadowing)
# --------------------------------------------------------------------------- #

@router.get(
    "/by-slug/{slug}",
    response_model=BarDetail,
    summary="Resolve a venue by its URL slug",
    description=(
        "Look up the full bar detail via its human-readable slug.  "
        "Useful for share links (`/bars/baczewski-lviv`) so the client "
        "doesn't need to know the numeric ID up-front."
    ),
)
async def get_venue_by_slug(
    slug: str,
    db: DbSession,
    viewer: OptionalViewer,
) -> BarDetail:
    result = await db.execute(select(Bar.id).where(Bar.slug == slug, Bar.deleted_at.is_(None)))
    bar_id: int | None = result.scalar_one_or_none()
    if bar_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="venue not found")
    return await bar_service.get_bar_detail(db, bar_id, viewer_id=viewer.id if viewer else None)


# --------------------------------------------------------------------------- #
# Detail by numeric ID
# --------------------------------------------------------------------------- #

@router.get(
    "/{venue_id}",
    response_model=BarDetail,
    summary="Full venue detail",
    description="Returns the complete bar record including photos, vibe tags, and recent reviews.",
)
async def get_venue(
    venue_id: int,
    db: DbSession,
    viewer: OptionalViewer,
) -> BarDetail:
    return await bar_service.get_bar_detail(
        db, venue_id, viewer_id=viewer.id if viewer else None
    )
