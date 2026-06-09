"""
Async SQLAlchemy engine + session factory.

We expose:
    - `engine`              — module-level async engine, created at import.
    - `AsyncSessionLocal`   — async session factory bound to that engine.
    - `Base`                — declarative base for ORM models (we'll start
                              adding domain models on top of the existing
                              schema as we wire each feature).
    - `get_session()`       — FastAPI dependency yielding a session that
                              commits on success and rolls back on error.
    - `dispose_engine()`    — called from the FastAPI lifespan on shutdown.

The DSN comes from `settings.database_url` and uses the `asyncpg` driver.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        str(settings.database_url),
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
    )


engine: AsyncEngine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that yields a transactional async session.

    Usage:
        @router.get("/things")
        async def list_things(db: AsyncSession = Depends(get_session)):
            ...

    The session is closed (and the connection returned to the pool) when the
    request finishes. The caller is responsible for committing when needed;
    on an unhandled exception the transaction is rolled back automatically.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Tear the engine down on app shutdown."""
    await engine.dispose()
