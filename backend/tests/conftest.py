"""
Pytest configuration + fixtures.

Tests run against a live local Postgres + Redis (the same `docker compose`
services the app uses). Each test gets a fresh transaction that is rolled
back at the end via a savepoint — so the DB state is identical between
tests without us having to re-create the schema.

To run the suite:

    docker compose up -d           # from the repo root
    uv run alembic upgrade head    # baseline schema applied
    uv run pytest

Tests skip themselves automatically if Postgres or Redis aren't reachable,
so a fresh checkout doesn't fail before the env is wired up.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.db import AsyncSessionLocal, engine, get_session
from app.core.redis import connect_redis, disconnect_redis
from app.main import app
from app.realtime.pubsub import start_pubsub, stop_pubsub


# --------------------------------------------------------------------------- #
# Skip the whole suite if backing services aren't reachable
# --------------------------------------------------------------------------- #
async def _services_up() -> bool:
    # Use a throwaway NullPool engine so the probe never checks a connection
    # out of the module-level engine's pool — otherwise that connection would
    # stay bound to this short-lived loop and break later session-scoped tests
    # ("attached to a different loop").
    probe = create_async_engine(str(settings.database_url), poolclass=NullPool)
    try:
        async with probe.connect() as conn:
            await conn.execute(text("SELECT 1"))
        redis = await connect_redis()
        await redis.ping()
        await disconnect_redis()
        return True
    except Exception:
        return False
    finally:
        await probe.dispose()


@pytest.fixture(scope="session", autouse=True)
def _skip_when_no_services():
    if not asyncio.run(_services_up()):
        pytest.skip(
            "Postgres or Redis unavailable. Run `docker compose up -d` "
            "and `uv run alembic upgrade head` first.",
            allow_module_level=True,
        )


# --------------------------------------------------------------------------- #
# Lifespan helpers: connect redis/pubsub for the whole test session
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture(scope="session")
async def _lifespan() -> AsyncIterator[None]:
    redis = await connect_redis()
    await start_pubsub(redis)
    yield
    await stop_pubsub()
    await disconnect_redis()
    # Close the engine pool while the shared session loop is still alive,
    # otherwise SQLAlchemy logs "Event loop is closed" during interpreter exit.
    await engine.dispose()


# --------------------------------------------------------------------------- #
# Per-test DB session (nested transaction → rollback)
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture
async def db_conn(_lifespan) -> AsyncIterator[AsyncConnection]:  # noqa: ARG001
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()


@pytest_asyncio.fixture
async def db(db_conn: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """
    Session bound to the outer transaction. We open a SAVEPOINT so commits
    inside the app code only commit to the savepoint — the outer `db_conn`
    fixture rolls back at the end of the test.
    """
    async with AsyncSession(bind=db_conn, expire_on_commit=False) as session:
        await session.begin_nested()

        # Re-open a SAVEPOINT every time the app code commits the inner nested
        # transaction, so the session stays usable for the rest of the test
        # while the outer `db_conn` transaction is what actually rolls back.
        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart(sess, transaction):  # pragma: no cover — invoked by SA
            if transaction.nested and not transaction._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            await session.close()


# --------------------------------------------------------------------------- #
# HTTP client
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """An httpx AsyncClient wired to the FastAPI app with the test DB session."""

    async def _override_session():
        yield db

    app.dependency_overrides[get_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Helpers shared by smoke tests
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture
async def signed_up_user(client: httpx.AsyncClient) -> dict:
    """Create a fresh user and return its body + tokens."""
    suffix = secrets.token_hex(4)
    payload = {
        "first_name": "Test",
        "username": f"tester_{suffix}",
        "email": f"test_{suffix}@taverntest.com",
        "password": "supersecret123",
        "main_city_id": 1,  # seeded city
    }
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture
async def auth_headers(signed_up_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {signed_up_user['tokens']['access_token']}"}


# Silence "unused" warnings on imported helpers in tests that only need fixtures.
_keep = (os, secrets)
