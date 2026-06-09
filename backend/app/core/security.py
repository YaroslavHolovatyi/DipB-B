"""
Security primitives: password hashing (Argon2) and JWT encode/decode.

We keep this module pure — no DB access, no FastAPI imports. Functions are
small, easy to test, and reusable from both the auth service and tests.

Two token flavours are issued:

    - **access**  — short-lived (`JWT_ACCESS_TOKEN_TTL_MIN` minutes), carries
                    the user id in `sub`. Sent on every API call.
    - **refresh** — long-lived (`JWT_REFRESH_TOKEN_TTL_DAYS` days), carries a
                    `jti` so the server can match it against a stored hash and
                    rotate/revoke at will.

The token type is encoded in a custom `type` claim so an access token cannot
be replayed as a refresh token (or vice-versa).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

# Argon2id with passlib defaults — fine for our scale; revisit memory/time
# cost when we have real perf data.
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time verify of a plaintext password against an Argon2 hash."""
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

TokenType = Literal["access", "refresh"]


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(*, subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """Issue a short-lived access token. `subject` is the user id."""
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_token_ttl_min)).timestamp()),
        "jti": uuid4().hex,
    }
    if extra:
        payload.update(extra)
    return _encode(payload)


def create_refresh_token(*, subject: str | int) -> tuple[str, str, datetime]:
    """
    Issue a refresh token.

    Returns ``(token, jti, expires_at)`` so the caller can persist the `jti`
    (or its hash) in `refresh_tokens` for later rotation/revocation.
    """
    now = _utcnow()
    expires_at = now + timedelta(days=settings.jwt_refresh_token_ttl_days)
    jti = uuid4().hex
    token = _encode(
        {
            "sub": str(subject),
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": jti,
        }
    )
    return token, jti, expires_at


def decode_token(token: str, *, expected_type: TokenType | None = None) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises ``jwt.PyJWTError`` on invalid signature/expired/etc., and a
    ``ValueError`` if the `type` claim does not match `expected_type`.
    """
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if expected_type is not None and payload.get("type") != expected_type:
        raise ValueError(f"expected token type {expected_type!r}, got {payload.get('type')!r}")
    return payload


# ---------------------------------------------------------------------------
# Refresh-token storage helpers
# ---------------------------------------------------------------------------
# The DB stores SHA-256 hashes of refresh JTIs, never the raw token. This way
# a DB leak doesn't hand attackers usable refresh tokens.


def hash_refresh_jti(jti: str) -> str:
    """SHA-256 hex digest of a refresh-token jti. Cheap, deterministic."""
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def generate_opaque_token(nbytes: int = 32) -> str:
    """
    Generate a URL-safe random token (used for one-off tokens like email
    verification, password reset, presigned share links, etc.).
    """
    return secrets.token_urlsafe(nbytes)
