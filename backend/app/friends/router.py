"""Friends router."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.friends import service
from app.friends.schemas import (
    FriendGroupCreate,
    FriendGroupMemberRead,
    FriendGroupRead,
    FriendRead,
    FriendRequestCreate,
    FriendRequestRead,
    UserSearchResult,
)

router = APIRouter(prefix="/friends", tags=["friends"])

# --------------------------------------------------------------------------- #
# Friend listings + requests
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[FriendRead])
async def list_friends(db: DbSession, user: CurrentUser) -> list[FriendRead]:
    return await service.list_friends(db, user.id)


@router.get("/search", response_model=list[UserSearchResult])
async def search_users(
    db: DbSession,
    user: CurrentUser,
    q: str = Query(min_length=2, max_length=64),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[UserSearchResult]:
    """Search all users by username or name, annotated with friendship status."""
    return await service.search_users(db, user.id, q, limit)


@router.get("/requests/incoming", response_model=list[FriendRequestRead])
async def incoming(db: DbSession, user: CurrentUser) -> list[FriendRequestRead]:
    return await service.list_incoming(db, user.id)


@router.get("/requests/outgoing", response_model=list[FriendRequestRead])
async def outgoing(db: DbSession, user: CurrentUser) -> list[FriendRequestRead]:
    return await service.list_outgoing(db, user.id)


@router.post(
    "/requests",
    response_model=FriendRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_request(
    payload: FriendRequestCreate, db: DbSession, user: CurrentUser
) -> FriendRequestRead:
    return await service.send_request(
        db, user.id, payload.recipient_id, payload.message
    )


@router.post("/requests/{request_id}/accept", response_model=FriendRequestRead)
async def accept_request(
    request_id: int, db: DbSession, user: CurrentUser
) -> FriendRequestRead:
    return await service.respond_to_request(db, user.id, request_id, accept=True)


@router.post("/requests/{request_id}/decline", response_model=FriendRequestRead)
async def decline_request(
    request_id: int, db: DbSession, user: CurrentUser
) -> FriendRequestRead:
    return await service.respond_to_request(db, user.id, request_id, accept=False)


@router.post("/requests/{request_id}/cancel", response_model=FriendRequestRead)
async def cancel_request(
    request_id: int, db: DbSession, user: CurrentUser
) -> FriendRequestRead:
    return await service.cancel_request(db, user.id, request_id)


# --------------------------------------------------------------------------- #
# Friend groups
# --------------------------------------------------------------------------- #
group_router = APIRouter(prefix="/friend-groups", tags=["friend-groups"])


@group_router.get("", response_model=list[FriendGroupRead])
async def list_groups(db: DbSession, user: CurrentUser) -> list[FriendGroupRead]:
    return await service.list_my_groups(db, user.id)


@group_router.post(
    "", response_model=FriendGroupRead, status_code=status.HTTP_201_CREATED
)
async def create_group(
    payload: FriendGroupCreate, db: DbSession, user: CurrentUser
) -> FriendGroupRead:
    return await service.create_group(
        db,
        user.id,
        name=payload.name,
        description=payload.description,
        image_url=payload.image_url,
        initial_member_ids=payload.initial_member_ids,
    )


@group_router.get(
    "/{group_id}/members", response_model=list[FriendGroupMemberRead]
)
async def list_members(
    group_id: int, db: DbSession, user: CurrentUser
) -> list[FriendGroupMemberRead]:
    return await service.list_group_members(db, user.id, group_id)


@group_router.post(
    "/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def add_member(
    group_id: int, user_id: int, db: DbSession, actor: CurrentUser
) -> None:
    await service.add_group_member(db, actor.id, group_id, user_id)


@group_router.delete(
    "/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    group_id: int, user_id: int, db: DbSession, actor: CurrentUser
) -> None:
    await service.remove_group_member(db, actor.id, group_id, user_id)
