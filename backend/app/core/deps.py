"""
Shared FastAPI dependencies.

These are imported by routers across every domain. Keeping them in one place
avoids circular imports and gives us a single audit point for things like
"how is the current user resolved?".
"""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.db import get_session
from app.core.security import decode_token

# `tokenUrl` is informational — Swagger uses it to build the "Authorize" dialog.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


DbSession = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    """
    Resolve the authenticated user from a Bearer access token.

    Raises 401 on missing/invalid/expired tokens. Use as:

        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            return user
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_error

    try:
        payload = decode_token(token, expected_type="access")
    except (jwt.PyJWTError, ValueError) as exc:  # noqa: F841 — exc available in debugger
        raise credentials_error from None

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise credentials_error from None

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_optional(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    """Same as `get_current_user`, but returns None instead of raising 401."""
    if not token:
        return None
    try:
        return await get_current_user(db, token)
    except HTTPException:
        return None
