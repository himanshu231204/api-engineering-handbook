# ORM Concepts

## Why This Matters

Most production API code never writes raw SQL — it calls ORM methods that generate SQL underneath. That's a huge productivity win, but it's also a leaky abstraction: the moment you don't understand what SQL your ORM is actually generating, you write code that silently issues hundreds of queries per request (the N+1 problem) or that can't express a query the ORM wasn't designed for. Understanding what an ORM does — and doesn't do — is what separates engineers who use SQLAlchemy well from engineers who get burned by it in production.

## Core Concept

An ORM (Object-Relational Mapper) maps between two fundamentally different ways of modeling data: your application's object graph (Python objects with attributes and references to other objects) and the database's relational model (tables, rows, foreign keys, joins). This gap is called the **impedance mismatch**: objects naturally express one-to-many and many-to-many relationships as nested collections (`user.orders` is a list), while a relational database expresses the same relationship as a foreign key column on a separate table with no inherent nesting. The ORM's job is to translate between these two representations so you can write `user.orders` in Python and have it turn into a `SELECT * FROM orders WHERE user_id = ?` behind the scenes.

Concretely, SQLAlchemy's ORM gives you:

- **Models**: Python classes that map to tables (columns become attributes).
- **Sessions**: a unit-of-work object that tracks changes to loaded objects and translates them into `INSERT`/`UPDATE`/`DELETE` statements when you commit.
- **Relationships**: declarative descriptions of foreign keys that let you navigate `user.orders` instead of writing joins by hand.
- **Query construction**: a Python API (`select()`, `.where()`, `.join()`) that builds SQL programmatically, composably, and safely (parameterized automatically).

## Mental Model

Think of the ORM session as a "shopping cart" for database changes. You load objects into it, modify their attributes in Python (`user.email = "new@example.com"`), and nothing hits the database until you call `commit()` — at which point the session diffs what changed and issues the minimal SQL to make the database match. This is the "unit of work" pattern: batch your changes, then flush them together in one transaction.

## How It Works

A SQLAlchemy model declares a table shape:

```python
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    total_cents: Mapped[int]
    user: Mapped["User"] = relationship(back_populates="orders")
```

When you write `select(User).where(User.id == 42)`, SQLAlchemy doesn't execute anything yet — it builds an abstract syntax representation of the query. Only `await session.execute(query)` sends it to the database. This laziness is intentional: it lets you compose query fragments (add a filter conditionally) before finalizing.

The **N+1 query trap** happens with relationships: if you fetch 20 users and then access `user.orders` for each one without telling SQLAlchemy to load orders eagerly, it issues one query per user (20 extra queries) on top of the original query that fetched the users — 21 queries total for data that could have been fetched in 1–2. This is introduced here conceptually; the full before/after fix with `selectinload` is in [Database Performance](database-performance.md).

## Architecture

```mermaid
flowchart TB
    subgraph App["Application Code"]
        A[Python objects: User, Order]
    end
    subgraph ORM["SQLAlchemy ORM Layer"]
        B[Session: unit of work]
        C[Query Builder: select/.where/.join]
        D[Identity Map: dedupes loaded objects]
    end
    subgraph DB["PostgreSQL"]
        E[Tables & Rows]
    end
    A <-->|attribute access, .add(), .commit()| B
    B --> C
    C -->|compiled SQL| E
    E -->|rows| C
    C --> D
    D --> A
```

## Request / Response Example

Python:

```python
result = await session.execute(select(User).where(User.email == "jane@example.com"))
user = result.scalar_one()
```

SQL generated:

```sql
SELECT users.id, users.email, users.full_name, users.created_at
FROM users
WHERE users.email = $1;
-- bound parameter: 'jane@example.com'
```

The ORM automatically parameterizes `$1` — you never construct this SQL string yourself, which is one of the ORM's underrated security benefits (see [SQL Injection](../10-api-security/sql-injection.md)).

## Code Example

```python
# Session usage inside a FastAPI route — the "unit of work" in action.
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@router.get("/users/{user_id}/orders")
async def list_user_orders(user_id: int, session: AsyncSession = Depends(get_session)):
    # selectinload eagerly fetches related orders in a second, batched query
    # instead of triggering one query per order access (the N+1 trap).
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.orders))
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    return {"orders": [{"id": o.id, "total_cents": o.total_cents} for o in user.orders]}


@router.post("/users/{user_id}/orders")
async def create_order(user_id: int, total_cents: int, session: AsyncSession = Depends(get_session)):
    order = Order(user_id=user_id, total_cents=total_cents, status="pending")
    session.add(order)          # staged in the unit of work, not yet in the DB
    await session.commit()      # flushes INSERT, commits the transaction
    await session.refresh(order)  # reloads server-generated fields (id, created_at)
    return {"id": order.id, "status": order.status}
```

```sql
-- When would you drop to raw SQL instead? Complex reporting queries,
-- window functions, or CTEs the ORM's query builder expresses awkwardly:
WITH ranked_orders AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
)
SELECT * FROM ranked_orders WHERE rn = 1;  -- most recent order per user
```

SQLAlchemy's `text()` construct (shown in [SQL Fundamentals](sql-fundamentals.md)) lets you run this directly while still using the same session and connection pool.

## Production Considerations

- Lazy-loaded relationships accessed inside a loop are the single most common source of API latency regressions in ORM-based codebases — always audit relationship access under load testing.
- `expire_on_commit=False` (shown in [PostgreSQL Integration](postgresql-integration.md)) avoids surprise re-fetches after commit, which matters for returning the just-created object in an API response.
- The ORM adds real CPU overhead (object hydration, change tracking) — for hot-path bulk operations (bulk inserts, analytics), raw SQL or bulk-insert APIs outperform the ORM significantly.

## Common Mistakes

- Accessing a lazy relationship (`user.orders`) inside a loop over many users — the N+1 trap.
- Forgetting `await session.commit()`, leaving changes only in memory.
- Treating ORM objects as safe to share across requests/async tasks — sessions are not thread-safe or task-safe; one session per request only.
- Reaching for complex ORM query-builder gymnastics when a five-line raw SQL query with `text()` would be clearer and faster to write.

## Best Practices

- Default to the ORM for standard CRUD; drop to raw SQL for reporting, bulk operations, or anything the query builder makes unreadable.
- Always eager-load relationships you know you'll access (`selectinload`, `joinedload`) rather than relying on lazy loading in an async context (lazy loading actually raises an error in async SQLAlchemy by default — a good forcing function).
- Keep one session per request, injected via a dependency, never a global session shared across requests.

## AI Engineering Perspective

When an LLM agent has a "database tool," you're effectively giving it ORM-like or SQL-like access. The impedance mismatch problem reappears in a new form: the agent thinks in terms of "get the user's orders," not "avoid N+1 queries" or "use the right isolation level." Wrapping database access behind a well-designed [Repository Pattern](repository-pattern.md) with a small number of well-tested methods — rather than exposing raw SQL execution to an agent — is the safer production pattern for AI agent tool design (see [Part 17 — AI Agents & MCP](../17-ai-agents-and-mcp/README.md)).

## Exercises

**Beginner**: Define a `Product` model with `id`, `name`, `price_cents`, and write a query to fetch all products under $20.

**Intermediate**: Add a `reviews` relationship to `Product`, write an endpoint that lists products with their review count, and use `selectinload` to avoid N+1 queries.

**Advanced**: Profile the same endpoint with and without `selectinload` under 50 products with 10 reviews each — count the number of SQL queries issued in both cases.

## Key Takeaways

- ORMs solve the impedance mismatch between object graphs and relational tables.
- The session implements a unit-of-work pattern: changes batch in memory, flush on commit.
- Lazy-loaded relationships are the root cause of the N+1 query trap — eager-load explicitly.
- Raw SQL is the right tool for complex reporting queries, bulk operations, and anything the ORM expresses awkwardly.
- Query construction (`select()`) is lazy — nothing hits the database until you `execute()`.

---
Previous: [PostgreSQL Integration](postgresql-integration.md) · Next: [Database Transactions](database-transactions.md) · Back to [Part 4 README](README.md)
