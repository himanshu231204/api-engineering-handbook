# PostgreSQL Integration

## Why This Matters

Choosing a database is one of the few decisions in API engineering that's expensive to reverse. PostgreSQL has become the default choice for good technical reasons, not just popularity, and knowing how to wire it into a FastAPI application correctly — asynchronously, safely, with proper connection lifecycle — is a foundational skill every backend engineer needs before touching anything more advanced.

## Core Concept

PostgreSQL ("Postgres") is an open-source, object-relational database known for strict standards compliance, strong transactional guarantees (full ACID, see [Database Transactions](database-transactions.md)), rich data types (JSONB, arrays, UUID, full-text search), and extensibility (extensions like PostGIS for geospatial data, pgvector for embeddings). Unlike MySQL's historically looser defaults or SQLite's single-writer model, Postgres is built for concurrent, multi-user, correctness-first workloads — exactly what a production API needs.

Why Postgres specifically over alternatives:

- **Correctness by default**: strict typing, real foreign key enforcement, no silent data truncation.
- **JSONB**: store and index semi-structured data without abandoning relational guarantees — useful for API payloads that have some optional/variable shape.
- **Concurrency model (MVCC)**: readers never block writers and vice versa, which matters for an API under real traffic.
- **Ecosystem**: pgvector for AI/embedding workloads (see [Part 16 — RAG APIs](../16-rag-apis/README.md)), mature tooling, every major cloud provider offers managed Postgres.

## Mental Model

Think of Postgres as a separate service your API talks to over the network (even if it's running on the same machine) — never as a library your code calls directly. That means every interaction crosses a socket: you open a connection, send a query, wait for a response, and (ideally) reuse that connection instead of opening a new one for every request. This network boundary is why connection management (see [Connection Pooling](connection-pooling.md)) becomes its own discipline.

## How It Works

Your FastAPI app doesn't speak Postgres's wire protocol directly — it goes through a driver. For async Python, that's `asyncpg` (a fast, Postgres-specific driver) wrapped by SQLAlchemy's async engine, which gives you a uniform API whether you're writing raw SQL or using the ORM (see [ORM Concepts](orm-concepts.md)).

The connection string format:

```
postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>
```

SQLAlchemy's `create_async_engine` parses this, creates a connection pool (see [Connection Pooling](connection-pooling.md)), and gives you `AsyncSession` objects to execute queries and manage transactions within your request handlers.

## Architecture

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant SQLAlchemy as SQLAlchemy AsyncEngine
    participant Pool as Connection Pool
    participant PG as PostgreSQL

    Client->>FastAPI: GET /users/42
    FastAPI->>SQLAlchemy: async with session
    SQLAlchemy->>Pool: acquire connection
    Pool->>PG: (reuse existing TCP connection)
    SQLAlchemy->>PG: SELECT * FROM users WHERE id = 42
    PG-->>SQLAlchemy: result rows
    SQLAlchemy-->>FastAPI: mapped object / dict
    FastAPI-->>Pool: release connection back to pool
    FastAPI-->>Client: 200 OK JSON
```

## Request / Response Example

```
GET /users/42 HTTP/1.1
Host: api.example.com
```

Resulting query issued by the app:

```sql
SELECT id, email, full_name, created_at FROM users WHERE id = 42;
```

Response:

```json
{
  "id": 42,
  "email": "jane@example.com",
  "full_name": "Jane Doe",
  "created_at": "2026-08-19T14:02:11.123Z"
}
```

## Code Example

```python
# db.py — engine and session setup, read once at app startup
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]
# e.g. postgresql+asyncpg://app_user:secret@db.internal:5432/app_db
# Never hardcode this — inject via environment variables (see Part 3:
# environment-variables.md).

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,        # steady-state connections kept open (see connection-pooling.md)
    max_overflow=5,      # extra connections allowed under burst load
    pool_pre_ping=True,  # validate a connection isn't stale before using it
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    """FastAPI dependency that yields a session per request and always closes it."""
    async with AsyncSessionLocal() as session:
        yield session
```

```python
# models.py — a minimal table definition using SQLAlchemy 2.0 typed models
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

```python
# routes.py — first real query from a FastAPI endpoint
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_session
from models import User

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "full_name": user.full_name}
```

This mirrors the dependency injection pattern from [Part 3 — Dependency Injection](../03-building-apis/dependency-injection.md): `get_session` is injected per request, guaranteeing cleanup even on exceptions.

## Production Considerations

- Always use `pool_pre_ping=True` in cloud environments — managed databases silently drop idle connections, and without pre-ping your first query on a stale connection fails.
- Set explicit `pool_size` and `max_overflow` — an unbounded pool can exhaust the database's `max_connections` limit under load (see [Connection Pooling](connection-pooling.md)).
- Use SSL (`sslmode=require` or driver equivalent) for connections crossing a network boundary, which is nearly always true in cloud deployments.
- Never construct `DATABASE_URL` with secrets in code — load from environment variables, consistent with [Part 3 — Environment Variables](../03-building-apis/environment-variables.md).

## Common Mistakes

- Using the sync `psycopg2` driver inside `async def` route handlers, which blocks the event loop and defeats the purpose of async FastAPI.
- Creating a new `create_async_engine()` per request instead of once at startup — this creates a new pool every time and leaks connections.
- Forgetting `pool_pre_ping`, leading to intermittent "connection reset" errors after periods of low traffic.
- Committing credentials into `DATABASE_URL` in source control.

## Best Practices

- One engine per process, created at startup, shared across all requests.
- Use `async_sessionmaker` + a FastAPI dependency (`get_session`) so every request gets an isolated session that's closed automatically.
- Keep the connection string entirely in environment variables, validated with Pydantic settings (see [Part 3 — Configuration Management](../03-building-apis/configuration-management.md)).
- Start with conservative pool sizes and tune based on observed concurrency, not guesses.

## AI Engineering Perspective

Postgres with the `pgvector` extension is a common choice for RAG systems that want to keep embeddings alongside relational metadata (user IDs, permissions, timestamps) in one transactional store, avoiding the operational overhead of a separate vector database for moderate-scale workloads. See [Part 16 — RAG APIs](../16-rag-apis/README.md) for when this is enough versus when you need a dedicated vector store.

## Exercises

**Beginner**: Set up a local Postgres instance (Docker: `docker run -e POSTGRES_PASSWORD=pw -p 5432:5432 postgres`) and connect to it with `psql`.

**Intermediate**: Extend the `examples/fastapi-crud/` project (currently SQLite) to use the `get_session`/`AsyncSessionLocal` pattern shown above against a local Postgres instance.

**Advanced**: Configure `pool_size`, `max_overflow`, and `pool_pre_ping`, then simulate connection loss (restart the Postgres container mid-traffic) and observe how your app recovers with and without `pool_pre_ping`.

## Key Takeaways

- Postgres is chosen for strict correctness, MVCC concurrency, JSONB, and ecosystem maturity (pgvector, extensions).
- Your API talks to Postgres over the network through a driver (`asyncpg`) — never treat it as an in-process library.
- SQLAlchemy's async engine + `AsyncSession` gives you a uniform interface for raw SQL and ORM queries.
- Create the engine once at startup; inject sessions per request via a dependency.
- Always load `DATABASE_URL` from environment variables, never hardcode it.

---
Previous: [SQL Fundamentals](sql-fundamentals.md) · Next: [ORM Concepts](orm-concepts.md) · Back to [Part 4 README](README.md)
