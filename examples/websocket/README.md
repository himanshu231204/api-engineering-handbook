# WebSocket Chat Room

A minimal, multi-client chat room built on FastAPI's WebSocket support. Multiple
browser tabs (or clients) connect to the same room, chat messages broadcast to
everyone in it, and joins/leaves are announced with system messages and a live
participant count.

Accompanies: [`docs/09-realtime-and-webhooks/websocket.md`](../../docs/09-realtime-and-webhooks/websocket.md)

## What This Demonstrates

- Accepting a WebSocket upgrade at a path with a parameter (`/ws/{room_id}`).
- A simple in-memory `ConnectionManager` that groups connections by room and
  broadcasts JSON messages to everyone in a room.
- Join/leave notifications and a live presence count.
- Handling `WebSocketDisconnect` cleanly so a dropped client doesn't leak a
  stale connection or crash the broadcast loop.
- A single self-contained `index.html` you can open in multiple browser tabs
  to try it out with zero frontend tooling.

## Prerequisites

- Python 3.11+

## How to Run

```bash
cd examples/websocket
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open **two or more browser tabs** at <http://localhost:8000/>. Pick a
username per tab (they can share the same room id, e.g. `general`), click
**Connect**, and start chatting — messages sent from one tab appear in all
connected tabs, along with join/leave/presence notices.

You can also connect with a plain WebSocket client, e.g.:

```bash
# using websocat, or any ws client
websocat "ws://localhost:8000/ws/general?username=bob"
```

## Things to Try / Modify

1. **Multiple rooms** — open tabs with different `room` values and confirm
   messages only broadcast within the same room, not across rooms.
2. **Simulate a dead connection** — kill a client ungracefully (close the
   terminal/tab without a clean WebSocket close) and confirm the server's
   `try/except` in `ConnectionManager.broadcast` removes it instead of
   erroring the whole broadcast.
3. **Scale beyond one process** — this example's `ConnectionManager` is an
   in-memory dict, so it only works within a single process. Sketch (or
   implement) how you'd swap the broadcast step for Redis Pub/Sub so a
   message sent to a client connected on server A reaches a client connected
   on server B. See
   [`docs/07-caching-performance/redis.md`](../../docs/07-caching-performance/redis.md)
   and [`docs/08-async-systems/message-queues.md`](../../docs/08-async-systems/message-queues.md).
4. **Add authentication** — right now `username` is a trusted query
   parameter. Replace it with a real token validated during the WebSocket
   handshake (see [`docs/05-authentication-authorization`](../../docs/05-authentication-authorization)).
