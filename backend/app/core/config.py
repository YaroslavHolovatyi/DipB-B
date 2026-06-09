"""
Application settings.

All runtime configuration is loaded from environment variables (or a `.env`
file in local development) via `pydantic-settings`. Import `settings` from
this module anywhere in the app — it is a singleton constructed at import time.

Adding a new setting:
    1. Add the field below with a default suitable for local dev.
    2. Add an entry to `.env.example` so other devs know it exists.
    3. (Optional) document any non-obvious behaviour in the field's docstring
       or in this module's docstring.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed wrapper around the process environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- App --------------------------------------------------------------------
    app_env: Literal["local", "staging", "production"] = "local"
    app_debug: bool = True
    app_host: str = "0.0.0.0"  # noqa: S104 — intentional for dev container
    app_port: int = 8000

    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8081",       # Expo Metro
            "http://localhost:19006",      # Expo web
            "exp://127.0.0.1:19000",       # Expo Go LAN
        ]
    )

    # -- Database ----------------------------------------------------------------
    # Async DSN — used by the app at runtime.
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://app:app@localhost:5432/beer_and_beverages"
    )
    # Sync DSN — used by Alembic (which historically prefers a sync driver).
    database_sync_url: PostgresDsn = Field(
        default="postgresql+psycopg://app:app@localhost:5432/beer_and_beverages"
    )

    # SQLAlchemy pool — sane defaults for a single Uvicorn worker.
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # -- Redis -------------------------------------------------------------------
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # -- JWT ---------------------------------------------------------------------
    jwt_secret: str = Field(
        default="dev-secret-do-not-use-in-prod",
        min_length=16,
        description="HMAC secret for signing JWTs. MUST be overridden in non-local envs.",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_min: int = 15
    jwt_refresh_token_ttl_days: int = 30

    # -- OpenAI ------------------------------------------------------------------
    openai_api_key: str | None = None
    openai_model_vision: str = "gpt-4o"
    openai_model_chat: str = "gpt-4o"

    # -- Object storage ----------------------------------------------------------
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_bucket: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    # --------------------------------------------------------------------------
    # Derived helpers
    # --------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: str | list[str]) -> list[str]:
        """Allow `CORS_ALLOW_ORIGINS=a,b,c` (string) in addition to a JSON list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


# Module-level convenience — most call sites just want `settings.foo`.
settings = get_settings()
