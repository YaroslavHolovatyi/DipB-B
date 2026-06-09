"""
Friends service.

Accepting a request inserts two `user_friends` rows in one transaction so
"my friends" stays a single indexed read. Declining / cancelling just
updates the request row.

Friend groups are simple owner-managed lists with role enum
(`member` / `admin`); the owner is always an `admin`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.friends.models import (
    FriendGroup,
    FriendGroupMember,
    FriendRequest,
    UserFriend,
)
from app.friends.schemas import (
    FriendGroupMemberRead,
    FriendGroupRead,
    FriendRead,
    FriendRequestRead,
    FriendUser,
)
from app.shared.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


# --------------------------------------------------------------------------- #
# Friend listings
# --------------------------------------------------------------------------- #
def _friend_user(u: User) -> FriendUser:
    return FriendUser(
        id=u.id,
        first_name=u.first_name,
        last_name=u.last_name,
        username=u.username,
        avatar_url=u.avatar_url,
        race_id=u.race_id,
    )


async def list_friends(db: AsyncSession, user_id: int) -> list[FriendRead]:
    rows = (
        await db.execute(
            select(UserFriend, User)
            .join(User, User.id == UserFriend.friend_id)
            .where(UserFriend.user_id == user_id, UserFriend.status == "accepted")
            .order_by(User.first_name)
        )
    ).all()
    return [
        FriendRead(
            user=_friend_user(u),
            nickname=link.nickname,
            is_muted=link.is_muted,
            accepted_at=link.accepted_at,
        )
        for link, u in rows
    ]


async def _ensure_not_already_friends(
    db: AsyncSession, a: int, b: int
) -> None:
    existing = await db.get(UserFriend, (a, b))
    if existing is not None and existing.status == "accepted":
        raise ConflictError("already friends")


# --------------------------------------------------------------------------- #
# Friend requests
# --------------------------------------------------------------------------- #
async def send_request(
    db: AsyncSession, sender_id: int, recipient_id: int, message: str | None
) -> FriendRequestRead:
    if sender_id == recipient_id:
        raise BadRequestError("cannot friend yourself")
    if (await db.get(User, recipient_id)) is None:
        raise NotFoundError("recipient not found")
    await _ensure_not_already_friends(db, sender_id, recipient_id)

    # Reject duplicate pending request
    existing = (
        await db.execute(
            select(FriendRequest).where(
                FriendRequest.sender_id == sender_id,
                FriendRequest.recipient_id == recipient_id,
                FriendRequest.status == "pending",
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("a pending request to this user already exists")

    row = FriendRequest(
        sender_id=sender_id, recipient_id=recipient_id, message=message
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return FriendRequestRead.model_validate(row)


async def list_incoming(db: AsyncSession, user_id: int) -> list[FriendRequestRead]:
    rows = (
        await db.execute(
            select(FriendRequest)
            .where(FriendRequest.recipient_id == user_id, FriendRequest.status == "pending")
            .order_by(FriendRequest.created_at.desc())
        )
    ).scalars().all()
    return [FriendRequestRead.model_validate(r) for r in rows]


async def list_outgoing(db: AsyncSession, user_id: int) -> list[FriendRequestRead]:
    rows = (
        await db.execute(
            select(FriendRequest)
            .where(FriendRequest.sender_id == user_id, FriendRequest.status == "pending")
            .order_by(FriendRequest.created_at.desc())
        )
    ).scalars().all()
    return [FriendRequestRead.model_validate(r) for r in rows]


async def respond_to_request(
    db: AsyncSession, user_id: int, request_id: int, *, accept: bool
) -> FriendRequestRead:
    req = await db.get(FriendRequest, request_id)
    if req is None or req.recipient_id != user_id:
        raise NotFoundError("request not found")
    if req.status != "pending":
        raise ConflictError("request is not pending")

    now = datetime.now(tz=UTC)
    req.responded_at = now

    if accept:
        req.status = "accepted"
        # Symmetric insert
        db.add_all(
            [
                UserFriend(
                    user_id=req.sender_id,
                    friend_id=req.recipient_id,
                    status="accepted",
                    accepted_at=now,
                ),
                UserFriend(
                    user_id=req.recipient_id,
                    friend_id=req.sender_id,
                    status="accepted",
                    accepted_at=now,
                ),
            ]
        )
    else:
        req.status = "declined"

    await db.commit()
    await db.refresh(req)
    return FriendRequestRead.model_validate(req)


async def cancel_request(
    db: AsyncSession, user_id: int, request_id: int
) -> FriendRequestRead:
    req = await db.get(FriendRequest, request_id)
    if req is None or req.sender_id != user_id:
        raise NotFoundError("request not found")
    if req.status != "pending":
        raise ConflictError("request is not pending")
    req.status = "cancelled"
    req.responded_at = datetime.now(tz=UTC)
    await db.commit()
    await db.refresh(req)
    return FriendRequestRead.model_validate(req)


# --------------------------------------------------------------------------- #
# Friend groups
# --------------------------------------------------------------------------- #
async def list_my_groups(db: AsyncSession, user_id: int) -> list[FriendGroupRead]:
    rows = (
        await db.execute(
            select(
                FriendGroup,
                func.count(FriendGroupMember.user_id).label("member_count"),
            )
            .join(FriendGroupMember, FriendGroupMember.group_id == FriendGroup.id)
            .where(FriendGroupMember.user_id == user_id)
            .group_by(FriendGroup.id)
            .order_by(FriendGroup.name)
        )
    ).all()
    return [
        FriendGroupRead(
            id=g.id,
            owner_id=g.owner_id,
            name=g.name,
            slug=g.slug,
            description=g.description,
            image_url=g.image_url,
            member_count=int(count),
        )
        for g, count in rows
    ]


async def create_group(
    db: AsyncSession,
    owner_id: int,
    *,
    name: str,
    description: str | None,
    image_url: str | None,
    initial_member_ids: list[int],
) -> FriendGroupRead:
    g = FriendGroup(
        owner_id=owner_id, name=name, description=description, image_url=image_url
    )
    db.add(g)
    await db.flush()
    # owner is always an admin member
    member_set = {owner_id, *initial_member_ids}
    for uid in member_set:
        db.add(
            FriendGroupMember(
                group_id=g.id,
                user_id=uid,
                role="admin" if uid == owner_id else "member",
            )
        )
    await db.commit()
    await db.refresh(g)
    return FriendGroupRead(
        id=g.id,
        owner_id=g.owner_id,
        name=g.name,
        slug=g.slug,
        description=g.description,
        image_url=g.image_url,
        member_count=len(member_set),
    )


async def list_group_members(
    db: AsyncSession, user_id: int, group_id: int
) -> list[FriendGroupMemberRead]:
    # only members can see member list
    if await db.get(FriendGroupMember, (group_id, user_id)) is None:
        raise ForbiddenError("not a member of this group")

    rows = (
        await db.execute(
            select(FriendGroupMember, User)
            .join(User, User.id == FriendGroupMember.user_id)
            .where(FriendGroupMember.group_id == group_id)
            .order_by(User.first_name)
        )
    ).all()
    return [
        FriendGroupMemberRead(
            user=_friend_user(u), role=m.role, joined_at=m.joined_at
        )
        for m, u in rows
    ]


async def add_group_member(
    db: AsyncSession, actor_id: int, group_id: int, user_id: int
) -> None:
    actor_membership = await db.get(FriendGroupMember, (group_id, actor_id))
    if actor_membership is None or actor_membership.role != "admin":
        raise ForbiddenError("only admins can add members")

    if await db.get(FriendGroupMember, (group_id, user_id)) is not None:
        return  # already a member — idempotent
    db.add(FriendGroupMember(group_id=group_id, user_id=user_id))
    await db.commit()


async def remove_group_member(
    db: AsyncSession, actor_id: int, group_id: int, user_id: int
) -> None:
    group = await db.get(FriendGroup, group_id)
    if group is None:
        raise NotFoundError("group not found")

    # The owner can never be removed via this endpoint.
    if user_id == group.owner_id:
        raise BadRequestError("cannot remove the group owner")

    # A user can remove themselves; an admin can remove anyone else
    actor_membership = await db.get(FriendGroupMember, (group_id, actor_id))
    if actor_membership is None:
        raise ForbiddenError("not a member of this group")
    if actor_id != user_id and actor_membership.role != "admin":
        raise ForbiddenError("only admins can remove other members")

    target = await db.get(FriendGroupMember, (group_id, user_id))
    if target is None:
        return  # idempotent
    await db.delete(target)
    await db.commit()


or_unused = or_  # silence unused import lint while keeping import for future use
