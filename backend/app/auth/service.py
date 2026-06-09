"""
Auth business logic.

All DB work for signup / login / refresh / logout lives here. The router
file is intentionally thin — it parses the request, calls one of these
functions, and serialises the result.

Refresh-token rotation
----------------------
Every successful `/auth/refresh` call:

    1. Looks up the incoming token's `jti` hash in `refresh_tokens`.
    2. Verifies it's not expired, not revoked, and belongs to the claimed user.
    3. Revokes the old row (`revoked_at = now()`).
    4. Issues a brand-new (access, refresh) pair and stores the new refresh hash.

This is the standard "rotating refresh tokens" pattern: a stolen refresh
token is usable exactly once, after which both the legitimate user and the
attacker get logged out on next refresh — a clear signal something's wrong.
"""

from __future__ import annotations

from datetime import UTC, datetime

import jwt
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, User
from app.auth.schemas import (
    AuthResponse,
    LoginRequest,
    SignupRequest,
    TokenPair,
    UserPublic,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_jti,
    verify_password,
)
from app.shared.exceptions import ConflictError, UnauthorizedError


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _tokens_for(user_id: int) -> tuple[TokenPair, str, datetime]:
    """Build a fresh ``TokenPair`` plus the (jti, expires_at) for the refresh row."""
    access = create_access_token(subject=user_id)
    refresh, jti, expires_at = create_refresh_token(subject=user_id)
    pair = TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_ttl_min * 60,
    )
    return pair, jti, expires_at


async def _persist_refresh(
    db: AsyncSession,
    *,
    user_id: int,
    jti: str,
    expires_at: datetime,
    ip: str | None = None,
    user_agent: str | None = None,
) -> RefreshToken:
    row = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_jti(jti),
        expires_at=expires_at,
        ip_address=ip,
        user_agent=user_agent,
    )
    db.add(row)
    await db.flush()
    return row


# --------------------------------------------------------------------------- #
# Signup
# --------------------------------------------------------------------------- #
async def signup(
    db: AsyncSession,
    payload: SignupRequest,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthResponse:
    """Create a new user and issue the first token pair."""
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        main_city_id=payload.main_city_id,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        # IntegrityError covers unique-collisions AND foreign-key / not-null
        # violations. Inspect the underlying Postgres error so we don't
        # mis-report a missing `cities` row as "email already in use".
        orig = getattr(exc, "orig", None)
        # asyncpg attaches these on its *Violation* exception classes.
        constraint = getattr(orig, "constraint_name", None)
        column = getattr(orig, "column_name", None)
        table = getattr(orig, "table_name", None)
        detail = getattr(orig, "detail", None)
        sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)

        if constraint and "email" in constraint:
            raise ConflictError("email is already in use") from exc
        if constraint and "username" in constraint:
            raise ConflictError("username is already in use") from exc
        # 23505 = unique_violation
        if sqlstate == "23505":
            raise ConflictError("username or email is already in use") from exc
        # 23502 = not_null_violation — asyncpg gives us the offending column.
        if sqlstate == "23502":
            raise ConflictError(
                f"could not create user: NOT NULL violation on "
                f"{table or 'users'}.{column or '<unknown column>'}"
            ) from exc
        # 23503 = foreign_key_violation (most likely main_city_id).
        if sqlstate == "23503":
            raise ConflictError(
                f"could not create user: foreign-key violation "
                f"({constraint or 'unknown constraint'}) — {detail or ''}".rstrip(" —")
            ) from exc
        raise ConflictError(
            f"could not create user: sqlstate={sqlstate} "
            f"constraint={constraint} column={column} detail={detail}"
        ) from exc

    tokens, jti, exp = _tokens_for(user.id)
    await _persist_refresh(db, user_id=user.id, jti=jti, expires_at=exp, ip=ip, user_agent=user_agent)
    await db.commit()
    await db.refresh(user)

    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #
async def login(
    db: AsyncSession,
    payload: LoginRequest,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthResponse:
    """Verify credentials and issue a fresh token pair."""
    ident = payload.identifier.strip()
    result = await db.execute(
        select(User).where(
            or_(User.email == ident, User.username == ident),
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    # Run verify even on a missing user so timing of a 401 doesn't leak
    # whether the identifier exists.
    placeholder_hash = (
        "$argon2id$v=19$m=65536,t=3,p=4$"
        "ZGVjb3lkZWNveWRlY295$aGFzaGhhc2hoYXNoaGFzaGhhc2hoYXNoaGFzaA"
    )
    candidate_hash = user.password_hash if user else placeholder_hash
    password_ok = verify_password(payload.password, candidate_hash)

    if user is None or not password_ok or not user.is_active:
        raise UnauthorizedError("invalid credentials")

    user.last_login_at = datetime.now(tz=UTC)

    tokens, jti, exp = _tokens_for(user.id)
    await _persist_refresh(db, user_id=user.id, jti=jti, expires_at=exp, ip=ip, user_agent=user_agent)
    await db.commit()

    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


# --------------------------------------------------------------------------- #
# Refresh
# --------------------------------------------------------------------------- #
async def refresh(
    db: AsyncSession,
    refresh_token: str,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> TokenPair:
    """Rotate a refresh token: revoke the old, issue a new pair."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except (jwt.PyJWTError, ValueError) as exc:
        raise UnauthorizedError("invalid refresh token") from exc

    try:
        user_id = int(payload["sub"])
        jti: str = payload["jti"]
    except (KeyError, TypeError, ValueError) as exc:
        raise UnauthorizedError("malformed refresh token") from exc

    token_hash = hash_refresh_jti(jti)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()

    now = datetime.now(tz=UTC)
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        raise UnauthorizedError("refresh token is not valid")

    # Rotate: revoke the old row, write a new one.
    row.revoked_at = now
    new_pair, new_jti, new_exp = _tokens_for(user_id)
    await _persist_refresh(db, user_id=user_id, jti=new_jti, expires_at=new_exp, ip=ip, user_agent=user_agent)
    await db.commit()
    return new_pair


# --------------------------------------------------------------------------- #
# Logout
# --------------------------------------------------------------------------- #
async def logout(db: AsyncSession, refresh_token: str) -> None:
    """Revoke a single refresh token. No-op if it was already invalid."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload["jti"]
    except (jwt.PyJWTError, ValueError, KeyError):
        # Don't leak whether the token was valid — logout is idempotent.
        return

    token_hash = hash_refresh_jti(jti)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if row is not None:
        row.revoked_at = datetime.now(tz=UTC)
        await db.commit()
