"""
FastAPI application entry-point.

Sets up:
    * Lifespan — connects Redis + starts the pub/sub bridge, tears them down.
    * CORS    — Expo dev server + production origins.
    * Routers — health, auth, realtime (websocket).
    * Error handlers — uniform JSON for unhandled exceptions in production.

Run locally:
    uv run fastapi dev app/main.py
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.achievements.router import router as achievements_router
from app.api.venues import router as venues_router
from app.auth.router import router as auth_router
from app.bars.router import router as bars_router
from app.chat.router import router as chat_router
from app.checks.router import router as checks_router
from app.core.config import settings
from app.core.db import dispose_engine
from app.core.redis import connect_redis, disconnect_redis
from app.friends.router import group_router as friend_groups_router
from app.friends.router import router as friends_router
from app.health.router import router as health_router
from app.notifications.router import router as notifications_router
from app.parties.router import router as parties_router
from app.quiz.router import router as quiz_router
from app.raids.router import router as raids_router
from app.realtime.pubsub import start_pubsub, stop_pubsub
from app.realtime.router import router as realtime_router
from app.reference.router import router as reference_router
from app.tavern_tales.router import router as tavern_tales_router
from app.users.router import router as users_router

logging.basicConfig(
    level=logging.INFO if not settings.app_debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("app")


# --------------------------------------------------------------------------- #
# Lifespan
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Connect external services on startup, tear them down on shutdown."""
    logger.info("starting Beer & Beverages backend v%s (env=%s)", __version__, settings.app_env)
    redis = await connect_redis()
    await start_pubsub(redis)
    try:
        yield
    finally:
        logger.info("shutting down")
        await stop_pubsub()
        await disconnect_redis()
        await dispose_engine()


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="Beer & Beverages API",
    version=__version__,
    debug=settings.app_debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — the Expo dev server hits us from a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Error handling
# --------------------------------------------------------------------------- #
@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unexpected errors.

    In production we hide the message — clients should see a generic 500.
    In dev we surface the actual exception text to make the stack trace
    obvious from the response.
    """
    logger.exception("unhandled exception: %s", exc)
    detail = str(exc) if settings.app_debug else "internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(venues_router)
app.include_router(users_router)
app.include_router(reference_router)
app.include_router(bars_router)
app.include_router(quiz_router)
app.include_router(friends_router)
app.include_router(friend_groups_router)
app.include_router(raids_router)
app.include_router(parties_router)
app.include_router(notifications_router)
app.include_router(checks_router)
app.include_router(achievements_router)
app.include_router(chat_router)
app.include_router(tavern_tales_router)
app.include_router(realtime_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Tiny root so curl-ing the base URL says something useful."""
    return {
        "service": "beer-and-beverages-api",
        "version": __version__,
        "docs": "/docs",
    }
