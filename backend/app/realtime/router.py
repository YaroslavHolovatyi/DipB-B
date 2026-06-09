"""
WebSocket endpoint.

The client opens a connection at:

    ws(s)://<host>/ws?token=<access_token>

We can't use the `Authorization` header here — RN's native WebSocket doesn't
support custom headers — so the access token comes through as a query
parameter. The token is the same short-lived JWT used for REST.

Frames are JSON. The server speaks one shape:

    { "type": "<event-type>", "data": { ... } }

…and accepts client frames of:

    { "type": "ping" }                          # liveness
    { "type": "delivery.ack", "data": { ... } } # message delivery receipt

Anything else is ignored for now — feature events will be added per domain.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_token
from app.realtime.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


def _resolve_user_id(token: str | None) -> int | None:
    """Decode the access token; return user id on success, None on failure."""
    if not token:
        return None
    try:
        payload = decode_token(token, expected_type="access")
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        return None


@router.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None, description="JWT access token"),
) -> None:
    user_id = _resolve_user_id(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)

    # Hello frame so clients can confirm they're authenticated.
    await websocket.send_json({"type": "hello", "data": {"user_id": user_id}})

    try:
        async for raw in websocket.iter_text():
            try:
                frame = json.loads(raw)
            except json.JSONDecodeError:
                continue
            await _dispatch_client_frame(websocket, user_id, frame)
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("ws handler crashed for user_id=%s", user_id)
    finally:
        await manager.disconnect(user_id, websocket)
        with contextlib.suppress(Exception):
            await websocket.close()


async def _dispatch_client_frame(
    websocket: WebSocket,
    user_id: int,  # noqa: ARG001 — will route per-user once feature events land
    frame: dict[str, object],
) -> None:
    """Handle incoming client frames. Tiny on purpose for now."""
    frame_type = frame.get("type")
    if frame_type == "ping":
        await websocket.send_json({"type": "pong"})
        return
    # `delivery.ack`, typing indicators, etc. will be wired up here as we
    # build the chat domain. Unknown types are silently ignored.
