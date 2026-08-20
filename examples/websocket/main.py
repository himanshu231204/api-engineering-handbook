"""
WebSocket chat-room example.

Demonstrates a FastAPI WebSocket endpoint (`/ws/{room_id}`) where any number
of clients can connect to the same room, broadcast messages to everyone else
in that room, and receive join/leave notifications. Connection state is kept
in a simple in-memory `ConnectionManager` — see the README for why that's
fine for a demo and what changes in a real multi-process deployment.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI(title="WebSocket Chat Room Example")


class ConnectionManager:
    """Tracks active WebSocket connections, grouped by room.

    This is deliberately just a dict of lists held in process memory. It
    works great for a single-process demo. It does NOT work if you scale
    to multiple server processes/instances, because a message broadcast by
    the manager in process A never reaches a client connected to process B.
    Production systems solve this by fanning broadcasts out through a shared
    pub/sub layer (e.g. Redis Pub/Sub) instead of an in-memory dict — see
    ../../docs/07-caching-performance/redis.md and
    ../../docs/08-async-systems/message-queues.md.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms.setdefault(room_id, []).append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        connections = self._rooms.get(room_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._rooms.pop(room_id, None)

    def room_size(self, room_id: str) -> int:
        return len(self._rooms.get(room_id, []))

    async def broadcast(self, room_id: str, message: dict, *, exclude: WebSocket | None = None) -> None:
        """Send `message` (as JSON) to every connection in the room.

        A connection that fails to receive the message (e.g. it dropped
        without a clean close) is dropped from the room instead of taking
        down the whole broadcast.
        """
        dead: list[WebSocket] = []
        for connection in self._rooms.get(room_id, []):
            if connection is exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)

        for connection in dead:
            self.disconnect(room_id, connection)


manager = ConnectionManager()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
async def index() -> FileResponse:
    """Serve the minimal HTML/JS test client."""
    return FileResponse("index.html")


@app.websocket("/ws/{room_id}")
async def chat_room(websocket: WebSocket, room_id: str, username: str = "anonymous") -> None:
    """Join `room_id` as `username` (a query param, e.g. ?username=alice).

    Message protocol (all JSON, all sent both ways):
        {"type": "chat", "username": "...", "text": "...", "at": "..."}
        {"type": "system", "text": "...", "at": "..."}
        {"type": "presence", "room_id": "...", "count": N}
    """
    await manager.connect(room_id, websocket)

    await manager.broadcast(
        room_id,
        {"type": "system", "text": f"{username} joined the room.", "at": _now()},
    )
    await manager.broadcast(
        room_id,
        {"type": "presence", "room_id": room_id, "count": manager.room_size(room_id)},
    )

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
                text = str(payload.get("text", ""))
            except (json.JSONDecodeError, AttributeError):
                # Be lenient: treat a non-JSON message as plain chat text.
                text = raw

            if not text.strip():
                continue

            await manager.broadcast(
                room_id,
                {"type": "chat", "username": username, "text": text, "at": _now()},
            )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(
            room_id,
            {"type": "system", "text": f"{username} left the room.", "at": _now()},
        )
        await manager.broadcast(
            room_id,
            {"type": "presence", "room_id": room_id, "count": manager.room_size(room_id)},
        )
