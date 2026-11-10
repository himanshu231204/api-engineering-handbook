# Test Databases

> [!TIP]
> **In one line:** Test against a real, disposable PostgreSQL that matches production, migrate it once, and isolate each test with a rolled-back transaction, because SQLite and mocks hide the bugs that matter.
>
> **In plain English:** A flight simulator is only useful if its controls behave like the real aircraft's. A test database is the simulator for your data layer, so it must be the same engine as production, and it must be reset between exercises so one pilot's crash does not start the next flight with a wrecked cockpit.
>
> **You'll be able to:** run Postgres in CI and locally with a service container or testcontainers · isolate tests with SQLAlchemy async transaction rollback and per-worker databases · build data with factories and apply migrations in tests

## Why This Matters

Most of what goes wrong in the data layer is invisible to a test that does not use a real database. A query that is correct in SQLite fails in Postgres because of a type rule. A unique constraint violation surfaces as an unhandled `IntegrityError` rather than a clean `409`. A `JSONB` operator, an `ILIKE`, an array column, `ON CONFLICT DO UPDATE`, a partial index, `SELECT ... FOR UPDATE SKIP LOCKED`, or a transaction isolation difference simply does not exist, or behaves differently, in the lightweight substitute. A migration that renames a column on a table with data works in an empty test schema and fails on a real one. These are exactly the bugs that reach production, and [integration tests](integration-testing.md) are the layer meant to catch them, but only if the database underneath is honest.

The opposite failure is just as common: a real database that is shared, never cleaned, and filled with leftovers. Tests that pass or fail depending on what an earlier test left behind, or on what a colleague's run is doing, destroy trust in the suite. A good test-database strategy therefore has two goals that pull in different directions: be realistic (same engine, same schema, same extensions as production) and be isolated (every test sees a known state, and tests can run in parallel). This chapter covers how to get both.

## Core Concept

A **test database** is a disposable database instance or schema, owned by the test run, that mirrors production's engine and schema. Four decisions define a strategy.

**1. Which engine?** Use the same one as production, at the same major version. Running Postgres 16 in production and SQLite in tests is the canonical false economy. SQLite has different type affinity (it is dynamically typed and will happily store a string in an integer column), different `NULL` and collation handling, no real concurrency model for writes, no `JSONB`, no arrays, and different DDL support (limited `ALTER TABLE`), so your tests pass on behaviour production will not exhibit and miss failures that production will. The speed advantage is small now that a Postgres container starts in a second or two and handles thousands of small tests per minute. Use SQLite in tests only if you also use it in production.

**2. How is the instance provided?** Two practical options:

- **A CI service container.** CI platforms such as GitHub Actions can start a Postgres container alongside your job and expose it on localhost with a health check. Fast, cheap, and declared in the workflow file.
- **Testcontainers.** The `testcontainers` library starts a throwaway Docker container from inside your test code, picks a free port, and removes the container when the run ends. It works the same on a laptop and in CI (any environment with a Docker daemon), and needs no manual `docker compose up`. The common pattern is to honour an environment variable such as `TEST_DATABASE_URL` when it is set (CI service container) and fall back to testcontainers when it is not (local).

**3. How does the schema get there?** Run your **real migrations** (Alembic's `upgrade head`) against the empty test database once per test session, instead of `Base.metadata.create_all()`. This tests the migrations themselves, so a broken or missing migration fails CI, and ensures the test schema matches what production will have, including indexes, constraints, and server defaults that exist only in migration files. `create_all` is a faster shortcut for tiny projects, with the risk that models and migrations silently diverge. A separate test that runs `upgrade head`, then `downgrade base`, then `upgrade head`, and one that checks `alembic check` reports no pending model changes, further protect against drift. See the migrations material in [Part 4](../04-databases-and-apis/README.md).

**4. How are tests isolated?** The standard technique is **transaction rollback per test**. Each test runs inside a database transaction that is never committed; at the end the transaction is rolled back, so the database returns to its starting state almost instantly, with no `DELETE`, `TRUNCATE`, or schema recreation. It is much faster than dropping and recreating tables, and it keeps tests independent. The alternatives are truncating tables after each test (slower, but needed when the code under test opens its own connections or runs in another process), recreating the schema (slowest, strongest), or a unique database per worker (needed for parallelism).

## Mental Model

Think of each test as writing in pencil on a transparent overlay laid on top of a printed page. The test can scribble, add rows, change values, and even "commit" by pressing hard, but the overlay is a savepoint on top of a transaction nobody will ever save. When the test ends you lift the overlay off and the page underneath is pristine. The printed page is the migrated schema, prepared once. Parallel workers each get their own copy of the printed page.

## How It Works

**Savepoint-based rollback in SQLAlchemy 2.0.** Application code under test usually calls `session.commit()`. If that really committed, nothing could be rolled back. The solution is to open a connection, begin an outer transaction on it, and bind the session to that connection with `join_transaction_mode="create_savepoint"`. In this mode, SQLAlchemy 2.0 turns the session's own `commit()` into the release of a `SAVEPOINT` inside the outer transaction rather than a real commit; the outer transaction is rolled back at the end of the test. A `session.rollback()` in the code under test rolls back to the savepoint. This is the pattern in SQLAlchemy's documentation for "joining a session into an external transaction". It relies on the database supporting savepoints (Postgres does) and on the driver handling them correctly (psycopg and asyncpg do; the SQLite drivers have known quirks that can make a "rolled-back" test leak data, yet another reason not to test against SQLite).

**Route the app's session to the test session.** FastAPI's `Depends(get_db)` is overridden with `app.dependency_overrides` so every request in the test uses the same savepoint-bound session; the test can then also query the database through that session and see exactly what the request wrote. Overrides must be cleared afterwards.

**Factories instead of fixtures files.** Build test data with small factory functions (or libraries such as `factory_boy` or `polyfactory`) that create valid rows with sensible, unique defaults and accept overrides for the fields a test cares about: `await make_user(db, role="admin")`. Compared with static SQL fixture files, factories keep each test's relevant data visible in the test itself, avoid uniqueness collisions through random suffixes, and survive schema changes because there is one place to update.

**When rollback is not enough.** The pattern assumes the code under test uses the single connection the test provided. Code that opens its own connection (background workers, a separate process, `LISTEN/NOTIFY` consumers) will not see the uncommitted data. Tests of that code need real commits and explicit cleanup, such as truncating the affected tables in teardown, in a database not shared with rollback-style tests. Also, behaviours that depend on commit boundaries, such as deferred constraints, isolation levels, or advisory-lock release, cannot be tested inside a wrapping transaction; give those a dedicated, committing test class.

**Parallel isolation.** With `pytest-xdist` running several workers, all workers must not share one database if they use committing tests, and even rollback tests can contend on locks and sequences. A robust approach is one database per worker: create `test_gw0`, `test_gw1`, and so on, from the `PYTEST_XDIST_WORKER` environment variable, migrate each once, and tear them down at the end. For large schemas you can create one migrated template database and clone it per worker with `CREATE DATABASE ... TEMPLATE ...` (the template must have no active connections while it is copied), which is faster than migrating N times. Per-worker databases also avoid sequence and lock interference.

**Speed levers.** Migrate once per session, not per test. Use rollback rather than recreate. Consider Postgres settings that trade durability for speed in an ephemeral test container: `fsync=off`, `synchronous_commit=off`, and `full_page_writes=off`, or mounting the data directory on tmpfs. These settings risk data loss on a crash, so use them only on throwaway test instances, never on anything you care about.

## Architecture

```mermaid
flowchart TB
    subgraph SESSION["Once per test session"]
        PG[("Postgres 16\nservice container or testcontainers")] --> DB["Create database per worker\n(test_gw0, test_gw1)"]
        DB --> MIG["alembic upgrade head"]
    end
    subgraph TEST["Per test"]
        CONN["Open connection\n+ begin outer transaction"] --> SESS["AsyncSession bound to connection\njoin_transaction_mode=create_savepoint"]
        SESS --> OVR["Override get_db\nwith this session"]
        OVR --> RUN["Run request + assertions\n(commit = release savepoint)"]
        RUN --> RB["Rollback outer transaction"]
    end
    MIG --> CONN
    RB -->|"database back to migrated state"| CONN
```

```mermaid
sequenceDiagram
    participant T as "Test"
    participant S as "Session"
    participant C as "Connection"
    participant P as "Postgres"
    T->>C: begin outer transaction
    T->>S: bind session, create_savepoint mode
    S->>P: SAVEPOINT sa_1 (on first use)
    T->>S: code under test calls commit()
    S->>P: RELEASE SAVEPOINT sa_1 (no real commit)
    T->>C: rollback outer transaction
    C->>P: ROLLBACK (all test data gone)
```

## Request / Response Example

The effect of isolation is visible at the HTTP level. Test A creates a user; test B, running right afterwards, sees none of it.

```http
POST /v1/users HTTP/1.1
Host: test
Content-Type: application/json

{"email": "ada@example.com", "name": "Ada"}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 1, "email": "ada@example.com", "name": "Ada"}
```

```http
GET /v1/users?email=ada@example.com HTTP/1.1
Host: test

HTTP/1.1 200 OK
{"items": [], "total": 0}
```

The second response happens in a later test: after the rollback, the table is empty again. If your suite ever returns `{"total": 1}` here, isolation has leaked. A real-database test also exercises genuine constraint behaviour: creating the same email twice yields `409 Conflict`, translated from Postgres's unique violation, which a mocked repository would never produce.

## Code Example

A `conftest.py` that provides Postgres (from `TEST_DATABASE_URL` in CI or testcontainers locally), a database per worker, real migrations applied through Alembic's connection-sharing pattern, and a savepoint-rolled-back session wired into FastAPI. It assumes `app.main.app`, `app.db.get_db`, and an Alembic `env.py` that uses a connection from `config.attributes["connection"]` when present. Add to `pytest.ini`: `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = session`, `asyncio_default_test_loop_scope = session` so the session-scoped engine and the tests share one event loop (option names are from recent pytest-asyncio releases; check your version).

```python
# tests/conftest.py
import os
import uuid
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db import get_db
from app.main import app


@pytest.fixture(scope="session")
def server_url() -> Iterator[str]:
    """URL of a Postgres server: CI service container, else testcontainers."""
    url = os.environ.get("TEST_DATABASE_URL")   # e.g. postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
    if url:
        yield url
        return
    # Local fallback: throwaway container (needs a Docker daemon).
    from testcontainers.postgres import PostgresContainer
    with PostgresContainer("postgres:16", driver="asyncpg") as pg:
        yield pg.get_connection_url()


def _upgrade(sync_conn) -> None:
    """Run the REAL migrations on the connection we are given."""
    cfg = Config("alembic.ini")
    cfg.attributes["connection"] = sync_conn    # env.py must use this when present
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def engine(server_url: str) -> AsyncIterator:
    # One database per xdist worker ("main" when not running in parallel).
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    name = f"test_{worker}"
    base = make_url(server_url)

    admin = create_async_engine(base, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()

    eng = create_async_engine(base.set(database=name))
    async with eng.begin() as conn:
        await conn.run_sync(_upgrade)           # migrate once per session
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncIterator[AsyncSession]:
    """A session whose commits are savepoint releases inside a rolled-back transaction."""
    async with engine.connect() as conn:
        outer = await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",   # commit() -> RELEASE SAVEPOINT
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()                       # everything the test did vanishes


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    async def _override() -> AsyncIterator[AsyncSession]:
        yield db                                         # the request uses the test's session
    app.dependency_overrides[get_db] = _override
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()


async def make_user(db: AsyncSession, **overrides):
    """Factory: valid, unique-by-default data; tests override only what they care about."""
    from app.models import User
    suffix = uuid.uuid4().hex[:8]
    user = User(**{"email": f"user-{suffix}@example.com", "name": "Test User", **overrides})
    db.add(user)
    await db.flush()                                     # assign id without committing
    return user
```

And the tests that use it:

```python
# tests/test_users.py
async def test_create_user_then_duplicate_is_409(client):
    body = {"email": "ada@example.com", "name": "Ada"}
    assert (await client.post("/v1/users", json=body)).status_code == 201
    assert (await client.post("/v1/users", json=body)).status_code == 409   # real unique constraint


async def test_isolation_between_tests(client):
    r = await client.get("/v1/users", params={"email": "ada@example.com"})
    assert r.json()["total"] == 0        # previous test's user was rolled back
```

The handler under test must translate `IntegrityError` into `409`. One caveat: after a database error inside a savepoint, the handler should roll back the session (which rolls back to the savepoint) before continuing to use it, otherwise the outer Postgres transaction is left in an aborted state.

## Production Considerations

- **Version parity.** Pin the test image to production's major version (`postgres:16`), and the same extensions (`pg_trgm`, `pgvector`, `postgis`). Use an image that includes them if you depend on them.
- **CI configuration.** In GitHub Actions use a `services: postgres:` block with a health check (`pg_isready`) so the job waits for readiness; see [ci-cd-testing-pipelines.md](ci-cd-testing-pipelines.md). Locally, the testcontainers fallback removes the "start the database first" step.
- **Startup cost.** Migrating a large schema can take tens of seconds. Do it once per session and per worker; for big schemas, build a migrated template database and clone it, or cache a schema dump as a CI artifact.
- **Concurrency tests need real commits.** Tests for race conditions, locking, and isolation levels need separate connections and committed data; isolate them with truncation or dedicated databases and mark them so they are not run in the rollback style.
- **Never point tests at a shared or production database.** Guard the fixture: refuse to run if the database name does not start with `test_`, to prevent a mistyped URL from dropping real data. The code above creates and drops only databases it names itself.
- **Test the migrations themselves.** Add a test that upgrades from an empty database to head and checks that downgrade and upgrade round-trip where you claim reversibility; migrate a database seeded with representative rows for risky changes.
- **Diagnose leaks.** If a test sees leftovers, check for code that creates its own engine or connection, for background tasks still running after the test, and for an un-awaited coroutine that commits late.

## Common Mistakes

- **SQLite standing in for Postgres,** and trusting the green result for queries, types, constraints, concurrency, and migrations it cannot model.
- **`create_all` instead of migrations,** so migration bugs and model/migration drift ship.
- **Truncating or recreating tables after every test** when rollback would be orders of magnitude faster.
- **Sharing one database across parallel workers** and getting intermittent lock waits and duplicate-key failures.
- **Letting the code under test commit for real,** because the session was not bound with savepoint mode, which leaks data into later tests.
- **Mocking the database session** in integration tests, which removes the constraint, query, and serialization behaviour you are trying to verify.
- **Hard-coded IDs and emails in tests,** causing collisions; use factories and unique values.
- **Order-dependent tests** that only pass because an earlier test seeded data.

## Best Practices

- Run the same Postgres major version and extensions as production, in a container, locally and in CI.
- Apply real migrations once per session, and test migrations separately.
- Isolate with outer-transaction rollback and `join_transaction_mode="create_savepoint"`; fall back to truncation only for tests that need real commits.
- Give each xdist worker its own database, optionally cloned from a migrated template.
- Build data with factories that generate unique, valid defaults and accept overrides.
- Make the fixtures refuse to run against a database that does not look like a test database.
- Keep tests independent: any test should pass alone, in any order, and in parallel.

## AI Engineering Perspective

AI features add data shapes that only a real engine can verify. Vector similarity search with `pgvector` (index type, distance operator, dimension mismatches) cannot be tested on SQLite or against a mock, because the interesting behaviour is the extension itself; use a Postgres image that bundles it and test your retrieval query with a handful of known embeddings you place at fixed positions, asserting the nearest-neighbour order. Likewise, conversation and agent state tables, token-usage ledgers, and idempotent tool-execution records depend on constraints and transactions that rollback-style tests exercise realistically. Seed embeddings with small deterministic vectors instead of calling an embedding model in tests. See [Part 16](../16-rag-apis/README.md) for retrieval and vector storage, and [Part 4](../04-databases-and-apis/README.md) for the database layer these tests protect.

## Exercises

**Beginner**
1. Start a Postgres container, point your test suite at it, and write two tests where the second asserts that the first test's inserted row is gone.

**Intermediate**
2. Replace `create_all` in your fixtures with an Alembic `upgrade head`, then add a test that runs `upgrade head`, `downgrade base`, `upgrade head`. Note what the migration run catches that `create_all` does not.
3. Run the suite with `pytest -n 4`. Add a database-per-worker fixture and measure the time versus a single shared database with rollback only.

**Advanced**
4. Write a test for a function that takes a row lock with `SELECT ... FOR UPDATE` and is called concurrently from two connections. Explain why it cannot use the rollback-per-test session, and how you isolate it.

## Key Takeaways

- Test against the same database engine and version as production; SQLite-for-Postgres tests give false confidence.
- Migrate with your real migrations once per session, then isolate each test with a rolled-back outer transaction and savepoint-mode sessions.
- Use one database per parallel worker and factories for unique, valid data.
- Code that opens its own connections or depends on commit boundaries needs committing tests with explicit cleanup.

### Check Yourself
<details markdown="1">
<summary>1. How does `join_transaction_mode="create_savepoint"` let code call `commit()` while the test still rolls everything back?</summary>

The session is bound to a connection that already has an outer transaction, and in this mode its `commit()` only releases a savepoint rather than committing for real. Rolling back the outer transaction at the end of the test then discards all changes.

</details>

<details markdown="1">
<summary>2. Why is running Alembic migrations in the test setup better than `Base.metadata.create_all()`?</summary>

Migrations are what production actually runs, so using them tests the migrations and guarantees the test schema includes indexes, constraints, and defaults defined there. `create_all` builds the schema from models and can silently drift from the migration history.

</details>

<details markdown="1">
<summary>3. Your suite passes with one worker but fails randomly with `pytest -n 4` against a single shared database. What is a robust fix?</summary>

Give each worker its own database (named from `PYTEST_XDIST_WORKER`), migrated once, so workers cannot collide on rows, sequences, or locks. Cloning from a migrated template database speeds this up for large schemas.

</details>

---
Back to the [Part 13 README](README.md).
