"""
WebSocket connection manager.

A single process can host many WebSocket connections at once. The manager is
the in-process registry — it answers "give me every socket belonging to user
42" so we can fan a message out. It does **not** know about Redis; the
pub/sub bridge (`pubsub.py`) calls into the manager when a message arrives
from another worker.

Multi-worker fan-out (high level)
---------------------------------
A typical chat message flow with N Uvicorn workers:

    1. Worker A handles the HTTP POST that creates the message.
    2. Worker A publishes `{type:"message.new", ...}` to a Redis channel
       (e.g. `conv:42`).
    3. The pubsub bridge on every worker is subscribed to that channel.
    4. Each worker's bridge calls `manager.broadcast_user(...)` for the
       local sockets that need the event.

The manager itself is intentionally tiny and dependency-free so we can unit
test it without Redis.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class ConnectionManager:
    """In-process registry of authenticated WebSockets, keyed by user id."""

    def __init__(self) -> None:
        # user_id -> set of live sockets (a user can have multiple devices).
        self._by_user: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Register an already-accepted socket against a user."""
        async with self._lock:
            self._by_user[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Drop a socket from the registry. Idempotent."""
        async with self._lock:
            sockets = self._by_user.get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._by_user.pop(user_id, None)

    # ------------------------------------------------------------------ #
    # Send / broadcast
    # ------------------------------------------------------------------ #
    async def send_to_socket(self, websocket: WebSocket, message: dict[str, Any]) -> bool:
        """Send a JSON payload to one socket. Returns False if the send failed."""
        if websocket.client_state != WebSocketState.CONNECTED:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            return False

    async def broadcast_user(self, user_id: int, message: dict[str, Any]) -> int:
        """
        Send a payload to every socket belonging to `user_id`. Returns the
        number of deliveries that succeeded. Dead sockets are pruned.
        """
        # Snapshot the set so we don't mutate while iterating.
        async with self._lock:
            sockets = list(self._by_user.get(user_id, ()))

        if not sockets:
            return 0

        delivered = 0
        dead: list[WebSocket] = []
        for ws in sockets:
            if await self.send_to_socket(ws, message):
                delivered += 1
            else:
                dead.append(ws)

        if dead:
            async with self._lock:
                live = self._by_user.get(user_id)
                if live is not None:
                    for ws in dead:
                        live.discard(ws)
                    if not live:
                        self._by_user.pop(user_id, None)

        return delivered

    # ------------------------------------------------------------------ #
    # Introspection (handy in /health later, and in tests)
    # ------------------------------------------------------------------ #
    def connection_count(self) -> int:
        return sum(len(s) for s in self._by_user.values())

    def is_online(self, user_id: int) -> bool:
        return bool(self._by_user.get(user_id))


# Module-level singleton — every part of the app that fans out an event
# imports this same instance.
manager = ConnectionManager()
