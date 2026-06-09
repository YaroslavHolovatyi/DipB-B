"""
Bars service.

The list query is the most interesting part: it composes optional filters
(FTS, city, price, vibe, rating), an optional "near me" geofilter via
PostGIS, and a left-join to `bar_favorites` so the response carries the
user's heart state. Everything is written in SQLAlchemy Core to keep the
SQL legible.
"""

from __future__ import annotations

from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import (
    Float,
    and_,
    desc,
    func,
    literal,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.bars.models import (
    Bar,
    BarFavorite,
    BarPhoto,
    BarReview,
    BarVibe,
)
from app.bars.schemas import (
    BarDetail,
    BarListParams,
    BarPhotoRead,
    BarReviewRead,
    BarSummary,
    BarVibeRead,
)
from app.reference.models import Vibe
from app.shared.exceptions import ConflictError, NotFoundError


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _bar_summary_columns(
    *, near_lat: float | None, near_lon: float | None, viewer_id: int | None
):
    """Common SELECT list for bar listing/detail endpoints."""
    distance = (
        func.ST_Distance(
            Bar.location,
            func.ST_SetSRID(func.ST_MakePoint(near_lon, near_lat), 4326).cast(
                # cast to geography so the result is in metres
                # see also: idx_bars_location on the geography column
                Bar.location.type
            ),
        )
        if near_lat is not None and near_lon is not None
        else literal(None).label("distance_m")
    )

    is_favorite = (
        select(literal(True))
        .where(BarFavorite.user_id == viewer_id, BarFavorite.bar_id == Bar.id)
        .exists()
        if viewer_id is not None
        else literal(False)
    )

    return (
        Bar.id,
        Bar.slug,
        Bar.name,
        Bar.city_id,
        Bar.address,
        Bar.image_url,
        Bar.price_category,
        Bar.rating_avg,
        Bar.rating_count,
        # ST_X/ST_Y are only defined for `geometry`; the column is `geography`,
        # so cast to geometry before projecting lon/lat.
        func.ST_Y(Bar.location.cast(Geometry)).cast(Float).label("latitude"),
        func.ST_X(Bar.location.cast(Geometry)).cast(Float).label("longitude"),
        distance.label("distance_m") if hasattr(distance, "label") else distance,
        is_favorite.label("is_favorite"),
    )


def _row_to_summary(row: tuple) -> BarSummary:
    (
        bar_id, slug, name, city_id, address, image_url, price_category,
        rating_avg, rating_count, latitude, longitude, distance_m, is_favorite,
    ) = row
    return BarSummary(
        id=bar_id,
        slug=slug,
        name=name,
        city_id=city_id,
        address=address,
        image_url=image_url,
        price_category=price_category,
        rating_avg=rating_avg,
        rating_count=rating_count,
        latitude=latitude,
        longitude=longitude,
        distance_m=distance_m,
        is_favorite=bool(is_favorite) if is_favorite is not None else False,
    )


# --------------------------------------------------------------------------- #
# List
# --------------------------------------------------------------------------- #
async def list_bars(
    db: AsyncSession, params: BarListParams, *, viewer_id: int | None
) -> tuple[list[BarSummary], int]:
    """Apply filters and return (items, total_count)."""
    cols = _bar_summary_columns(
        near_lat=params.near_lat, near_lon=params.near_lon, viewer_id=viewer_id
    )

    stmt = select(*cols).select_from(Bar).where(
        Bar.is_active.is_(True), Bar.deleted_at.is_(None)
    )
    count_stmt = select(func.count(Bar.id)).where(
        Bar.is_active.is_(True), Bar.deleted_at.is_(None)
    )

    if params.q:
        # Combine FTS + trigram similarity; FTS is fast on long tokens, trigram
        # catches typos and short words.
        q_tsquery = func.plainto_tsquery("simple", params.q)
        text_filter = or_(
            Bar.__table__.c.search_vector.op("@@")(q_tsquery),
            func.similarity(Bar.name, params.q) > 0.2,
        )
        stmt = stmt.where(text_filter)
        count_stmt = count_stmt.where(text_filter)

    if params.city_id is not None:
        stmt = stmt.where(Bar.city_id == params.city_id)
        count_stmt = count_stmt.where(Bar.city_id == params.city_id)

    if params.price_category is not None:
        stmt = stmt.where(Bar.price_category == params.price_category)
        count_stmt = count_stmt.where(Bar.price_category == params.price_category)

    if params.min_rating is not None:
        stmt = stmt.where(Bar.rating_avg >= params.min_rating)
        count_stmt = count_stmt.where(Bar.rating_avg >= params.min_rating)

    if params.vibe_id is not None:
        stmt = stmt.join(BarVibe, BarVibe.bar_id == Bar.id).where(BarVibe.vibe_id == params.vibe_id)
        count_stmt = (
            count_stmt.select_from(Bar.__table__.join(BarVibe.__table__, BarVibe.bar_id == Bar.id))
            .where(BarVibe.vibe_id == params.vibe_id)
        )

    if (
        params.near_lat is not None
        and params.near_lon is not None
        and params.radius_m is not None
    ):
        point = func.ST_SetSRID(
            func.ST_MakePoint(params.near_lon, params.near_lat), 4326
        ).cast(Bar.location.type)
        geo_filter = func.ST_DWithin(Bar.location, point, params.radius_m)
        stmt = stmt.where(geo_filter)
        count_stmt = count_stmt.where(geo_filter)
        # Sort closest-first when "near me" is in play
        stmt = stmt.order_by("distance_m")
    else:
        # Default sort: rating desc, then name
        stmt = stmt.order_by(desc(Bar.rating_avg), Bar.name)

    stmt = stmt.limit(params.limit).offset(params.offset)

    rows = (await db.execute(stmt)).all()
    total = (await db.execute(count_stmt)).scalar_one()
    return [_row_to_summary(r) for r in rows], int(total)


# --------------------------------------------------------------------------- #
# Detail
# --------------------------------------------------------------------------- #
async def get_bar_detail(db: AsyncSession, bar_id: int, *, viewer_id: int | None) -> BarDetail:
    bar = await db.get(Bar, bar_id)
    if bar is None or bar.deleted_at is not None:
        raise NotFoundError("bar not found")

    cols = _bar_summary_columns(near_lat=None, near_lon=None, viewer_id=viewer_id)
    row = (
        await db.execute(select(*cols).where(Bar.id == bar_id))
    ).one()
    summary = _row_to_summary(row)

    photos = (
        await db.execute(
            select(BarPhoto).where(BarPhoto.bar_id == bar_id).order_by(BarPhoto.position)
        )
    ).scalars().all()

    vibes_rows = (
        await db.execute(
            select(Vibe.id, Vibe.slug, Vibe.name)
            .join(BarVibe, BarVibe.vibe_id == Vibe.id)
            .where(BarVibe.bar_id == bar_id)
            .order_by(Vibe.name)
        )
    ).all()

    reviews = (
        await db.execute(
            select(BarReview)
            .where(BarReview.bar_id == bar_id)
            .order_by(BarReview.created_at.desc())
            .limit(10)
        )
    ).scalars().all()

    return BarDetail(
        **summary.model_dump(),
        description=bar.description,
        phone=bar.phone,
        website=bar.website,
        work_hours=bar.work_hours or {},
        photos=[BarPhotoRead.model_validate(p) for p in photos],
        vibes=[BarVibeRead(id=v.id, slug=v.slug, name=v.name) for v in vibes_rows],
        recent_reviews=[BarReviewRead.model_validate(r) for r in reviews],
    )


# --------------------------------------------------------------------------- #
# Favorites
# --------------------------------------------------------------------------- #
async def add_favorite(db: AsyncSession, user_id: int, bar_id: int) -> None:
    bar = await db.get(Bar, bar_id)
    if bar is None or bar.deleted_at is not None:
        raise NotFoundError("bar not found")
    existing = await db.get(BarFavorite, (user_id, bar_id))
    if existing is not None:
        return
    db.add(BarFavorite(user_id=user_id, bar_id=bar_id))
    await db.commit()


async def remove_favorite(db: AsyncSession, user_id: int, bar_id: int) -> None:
    existing = await db.get(BarFavorite, (user_id, bar_id))
    if existing is None:
        return
    await db.delete(existing)
    await db.commit()


async def list_my_favorites(db: AsyncSession, user_id: int) -> list[BarSummary]:
    cols = _bar_summary_columns(near_lat=None, near_lon=None, viewer_id=user_id)
    stmt = (
        select(*cols)
        .join(BarFavorite, and_(BarFavorite.bar_id == Bar.id, BarFavorite.user_id == user_id))
        .where(Bar.deleted_at.is_(None))
        .order_by(BarFavorite.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [_row_to_summary(r) for r in rows]


# --------------------------------------------------------------------------- #
# Reviews
# --------------------------------------------------------------------------- #
async def upsert_review(
    db: AsyncSession, user_id: int, bar_id: int, rating: int, text: str | None
) -> BarReviewRead:
    bar = await db.get(Bar, bar_id)
    if bar is None or bar.deleted_at is not None:
        raise NotFoundError("bar not found")

    existing = (
        await db.execute(
            select(BarReview).where(
                BarReview.bar_id == bar_id, BarReview.user_id == user_id
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.rating = rating
        existing.text = text
        row = existing
    else:
        row = BarReview(bar_id=bar_id, user_id=user_id, rating=rating, text=text)
        db.add(row)

    # Refresh the denormalised cache (cheap on the small expected review count).
    await db.flush()
    agg = (
        await db.execute(
            select(func.avg(BarReview.rating), func.count(BarReview.id)).where(
                BarReview.bar_id == bar_id
            )
        )
    ).one()
    bar.rating_avg = Decimal(str(round(float(agg[0] or 0), 2)))
    bar.rating_count = int(agg[1] or 0)

    await db.commit()
    await db.refresh(row)
    return BarReviewRead.model_validate(row)


async def delete_review(db: AsyncSession, user_id: int, bar_id: int) -> None:
    existing = (
        await db.execute(
            select(BarReview).where(
                BarReview.bar_id == bar_id, BarReview.user_id == user_id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        raise NotFoundError("review not found")
    await db.delete(existing)
    # Refresh denorm cache
    bar = await db.get(Bar, bar_id)
    if bar is not None:
        agg = (
            await db.execute(
                select(func.avg(BarReview.rating), func.count(BarReview.id)).where(
                    BarReview.bar_id == bar_id
                )
            )
        ).one()
        bar.rating_avg = Decimal(str(round(float(agg[0] or 0), 2)))
        bar.rating_count = int(agg[1] or 0)
    await db.commit()


# Re-export so type checkers see ConflictError as imported
__all__ = ["list_bars", "get_bar_detail", "add_favorite", "remove_favorite",
           "list_my_favorites", "upsert_review", "delete_review", "ConflictError"]
