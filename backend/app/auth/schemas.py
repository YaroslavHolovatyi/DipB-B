"""
Pydantic schemas for the auth endpoints.

Naming convention:
    *Request    — input from the client
    *Response   — output to the client
    UserPublic  — the safe-to-serialise user shape (never includes hash, etc.)
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --------------------------------------------------------------------------- #
# User
# --------------------------------------------------------------------------- #
class UserPublic(BaseModel):
    """The user object we return to clients. No secrets here."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str | None = None
    username: str
    # Plain `str`, not EmailStr: this is an OUTPUT model echoing an already
    # stored/validated address. Re-validating here rejects reserved test
    # domains like `*.test` (e.g. the seeded admin@tavern.test). New signups
    # are still validated via EmailStr on SignupRequest below.
    email: str
    avatar_url: str | None = None
    bio: str | None = None
    main_city_id: int
    race_id: int | None = None
    gender: str | None = None
    role: str
    is_active: bool
    social_rating: int = 100
    events_attended: int = 0
    events_ditched: int = 0
    email_verified_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Tokens
# --------------------------------------------------------------------------- #
class TokenPair(BaseModel):
    """The token envelope returned by signup / login / refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expires


class AuthResponse(BaseModel):
    """Signup + login response — tokens plus the user we just authenticated."""

    user: UserPublic
    tokens: TokenPair


# --------------------------------------------------------------------------- #
# Requests
# --------------------------------------------------------------------------- #
class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    main_city_id: int = Field(ge=1)


class LoginRequest(BaseModel):
    # Accept either an email *or* a username in the same field — the service
    # layer figures out which it is.
    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
