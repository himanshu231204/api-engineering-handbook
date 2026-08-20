# Project 6 — Real-Time Chat API

## Goal

Build a WebSocket-based chat system with rooms/channels, persisted message history, presence tracking, and pagination through the past. This is the project where "real-time" stops being an abstract concept and becomes a concrete engineering problem: managing long-lived connections, broadcasting to the right subset of clients, reconciling in-memory connection state with a database of record, and handling reconnects gracefully without losing messages.

## Builds On

- [Part 9 — Real-Time APIs](../../docs/09-realtime-and-webhooks/README.md)
- Specifically: [WebSocket](../../docs/09-realtime-and-webhooks/websocket.md), [polling](../../docs/09-realtime-and-webhooks/polling.md), [Server-Sent Events](../../docs/09-realtime-and-webhooks/server-sent-events.md) (for comparison)
- Recommended pairing: [Project 2 — Authentication Service](../02-authentication-service/README.md) for identifying connected users
- Also relevant: [pagination](../../docs/02-rest-api-design/pagination.md) for message history

## Requirements

- Users authenticate (via a JWT passed during the WebSocket handshake) before joining any room.
- Users can join/leave rooms; messages sent to a room are broadcast only to clients currently connected to that room.
- Every message is persisted before (or atomically with) being broadcast — a client that reconnects must be able to fetch history, not just future messages.
- `GET /rooms/{id}/messages` supports cursor-based pagination through history (newest-first, load-more-on-scroll-up semantics).
- Presence: the API can report which users are currently connected to a room, and broadcasts `user.joined`/`user.left` events.
- Typing indicators (ephemeral, not persisted) are broadcast to a room.
- Reconnection is handled gracefully: a client that reconnects with a `last_seen_message_id` receives any messages it missed via REST before resuming the live WebSocket stream.
- The system supports multiple server instances broadcasting to the same room (a hint that in-memory-only connection tracking doesn't scale — see Advanced Improvements).

## Architecture

```mermaid
flowchart LR
    ClientA[Client A] <-->|WebSocket /ws/rooms/id| Gateway[WebSocket Gateway]
    ClientB[Client B] <-->|WebSocket /ws/rooms/id| Gateway
    Gateway --> ConnMgr[Connection Manager\n(in-memory room -> sockets)]
    Gateway -->|persist first| MsgDB[(messages table)]
    Gateway --> Presence[(Presence Store\nRedis)]
    ClientA -->|GET /rooms/id/messages\n(history, pagination)| API[REST API]
    API --> MsgDB
    Gateway -.->|pub/sub for multi-instance fanout| PubSub[(Redis Pub/Sub)]
```

## API Endpoints

| Method/Protocol | Path | Description |
|---|---|---|
| POST | `/rooms` | Create a new chat room. |
| GET | `/rooms` | List rooms the authenticated user is a member of. |
| POST | `/rooms/{id}/join` | Join a room (adds membership record). |
| POST | `/rooms/{id}/leave` | Leave a room. |
| GET | `/rooms/{id}/messages` | Paginated message history, `?before=<message_id>&limit=50`, newest-first. |
| GET | `/rooms/{id}/presence` | List currently-connected users in the room. |
| WS | `/ws/rooms/{id}` | WebSocket connection; requires `?token=<jwt>`. Sends/receives JSON events: `message.send`, `message.new`, `typing.start`, `typing.stop`, `user.joined`, `user.left`. |
| GET | `/rooms/{id}/messages/since` | REST fallback for reconnect: `?last_seen_message_id=<id>` returns missed messages before resuming the socket. |

### WebSocket Event Shapes

| Event (client → server) | Payload | Event (server → client) | Payload |
|---|---|---|---|
| `message.send` | `{ content }` | `message.new` | `{ id, room_id, user_id, content, created_at }` |
| `typing.start` / `typing.stop` | `{}` | `typing.update` | `{ user_id, typing: bool }` |
| — | — | `user.joined` / `user.left` | `{ user_id, room_id }` |

## Database Schema

```sql
CREATE TABLE rooms (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL,
    created_by     UUID NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE room_members (
    room_id        UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id        UUID NOT NULL,
    joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (room_id, user_id)
);

CREATE TABLE messages (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id        UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id        UUID NOT NULL,
    content        TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_room_created ON messages (room_id, created_at DESC);

-- Presence is typically kept in Redis, not Postgres, but a fallback table:
CREATE TABLE presence_fallback (
    room_id        UUID NOT NULL,
    user_id        UUID NOT NULL,
    connected_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_ping_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (room_id, user_id)
);
```

## Suggested Folder Structure

```
06-realtime-chat/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── rooms.py
│   │   └── messages.py
│   ├── ws/
│   │   ├── gateway.py            # WebSocket endpoint, auth handshake
│   │   ├── connection_manager.py # in-memory room -> active sockets
│   │   └── events.py             # event type definitions/schemas
│   ├── schemas/
│   │   ├── room.py
│   │   └── message.py
│   ├── services/
│   │   ├── room_service.py
│   │   ├── message_service.py
│   │   └── presence_service.py
│   ├── pubsub/
│   │   └── redis_pubsub.py       # multi-instance fanout
│   ├── models/
│   │   ├── room.py
│   │   └── message.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_ws_auth.py
│   ├── test_message_broadcast.py
│   ├── test_history_pagination.py
│   └── test_reconnect_missed_messages.py
├── requirements.txt
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold FastAPI project with Postgres for messages/rooms and Redis for presence and pub/sub.
2. Implement `rooms` and `room_members` tables plus `POST /rooms`, `GET /rooms`, `POST /rooms/{id}/join`/`leave`.
3. Implement JWT verification during the WebSocket handshake (token passed as a query param or subprotocol, since browsers can't set custom headers on `WebSocket`), reusing the auth patterns from [Project 2](../02-authentication-service/README.md) or [bearer tokens](../../docs/05-authentication-authorization/bearer-tokens.md).
4. Build the `ConnectionManager`: an in-memory `dict[room_id, set[WebSocket]]` with `connect`, `disconnect`, and `broadcast(room_id, event)` methods.
5. Implement the core message flow: on `message.send`, persist to `messages` first, then broadcast `message.new` to all connections in that room — persistence must not be skipped even under load.
6. Implement `GET /rooms/{id}/messages` with cursor-based pagination (`before=<message_id>`, `limit`), per [pagination](../../docs/02-rest-api-design/pagination.md).
7. Implement presence: on connect, add the user to a Redis set for the room and broadcast `user.joined`; on disconnect, remove and broadcast `user.left`; expose `GET /rooms/{id}/presence`.
8. Implement typing indicators as fire-and-forget broadcast events (`typing.start`/`typing.stop`) that are never persisted to the database.
9. Implement the reconnect flow: client stores the last message ID it saw; on reconnect it calls `GET /rooms/{id}/messages/since?last_seen_message_id=...` to backfill before resubscribing to the socket.
10. Handle disconnects cleanly: catch `WebSocketDisconnect`, remove the connection from `ConnectionManager` and presence, and broadcast `user.left` even on ungraceful drops (use a heartbeat/ping-pong timeout to detect zombie connections).
11. Write integration tests using two simulated WebSocket clients in the same room to verify broadcast fan-out, and a third in a different room to verify isolation.
12. Load-test with many concurrent connections in one room to observe where a single-process, in-memory `ConnectionManager` starts to strain.

## Advanced Improvements

- Introduce Redis Pub/Sub (or a message broker) so multiple API server instances can broadcast to clients connected to *other* instances — the single-process `ConnectionManager` doesn't scale past one node.
- Add message editing/deletion with soft-delete markers and broadcast `message.updated`/`message.deleted` events.
- Add read receipts and unread counts per user per room.
- Add rate limiting per connection to prevent message-flood abuse.
- Add file/image attachments to messages, reusing the upload pattern from [Project 5](../05-document-processing/README.md).
- Add direct (1:1) messages as a special two-member room type.

## Production Checklist

- [ ] WebSocket connections authenticated before any room join is allowed; unauthenticated sockets are rejected immediately.
- [ ] Connection state horizontally scalable via Redis pub/sub, not trapped in a single process's memory.
- [ ] Heartbeat/ping-pong to detect and clean up dead connections (clients don't always send a clean close frame).
- [ ] Backpressure handling: a slow client shouldn't block broadcasts to fast clients (per-connection send queues with bounded size).
- [ ] Message persistence happens before/atomically with broadcast — no message is ever broadcast-only and lost on crash.
- [ ] Rate limiting on message sends per user/connection to prevent spam and resource exhaustion.
- [ ] Connection count and per-room fan-out latency exported as metrics for capacity planning.
- [ ] Graceful shutdown: in-flight connections are notified/drained instead of dropped on deploy.
- [ ] Input sanitization on message content (no unescaped HTML if rendered client-side — XSS surface).
- [ ] Load tested for target concurrent-connection count per instance before committing to a capacity plan.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Pairs with: [Project 2 — Authentication Service](../02-authentication-service/README.md)
