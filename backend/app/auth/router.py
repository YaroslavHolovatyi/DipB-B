"""
Auth router — thin wrapper around `app.auth.service`.

Endpoints:
    POST /auth/signup    — create account, return tokens + user
    POST /auth/login     — verify credentials, return tokens + user
    POST /auth/refresh   — rotate refresh token, return new pair
    POST /auth/logout    — revoke a refresh token
    GET  /auth/me        — echo the authenticated user
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Request, status

from app.auth import service
from app.auth.schemas import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    TokenPair,
    UserPublic,
)
from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    """Pull (ip, user-agent) out of the request for the refresh-token row."""
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip, user_agent


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def signup(
    payload: SignupRequest,
    db: DbSession,
    request: Request,
) -> AuthResponse:
    ip, ua = _client_meta(request)
    return await service.signup(db, payload, ip=ip, user_agent=ua)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Log in with email-or-username + password",
)
async def login(
    payload: LoginRequest,
    db: DbSession,
    request: Request,
) -> AuthResponse:
    ip, ua = _client_meta(request)
    return await service.login(db, payload, ip=ip, user_agent=ua)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate the refresh token (returns a brand-new pair)",
)
async def refresh(
    payload: RefreshRequest,
    db: DbSession,
    request: Request,
) -> TokenPair:
    ip, ua = _client_meta(request)
    return await service.refresh(db, payload.refresh_token, ip=ip, user_agent=ua)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
)
async def logout(
    payload: LogoutRequest,
    db: DbSession,
) -> None:
    await service.logout(db, payload.refresh_token)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Return the authenticated user",
)
async def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


# Re-export so type-checkers see CurrentUser as used.
__all__ = ["router", "Annotated"]
