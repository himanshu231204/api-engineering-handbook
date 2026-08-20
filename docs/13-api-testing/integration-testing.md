# Integration Testing

## Why This Matters

`unit-testing.md` proved your discount math is correct in isolation. But your API's actual failure modes rarely live in isolated pure functions — they live at the seams: does the route handler correctly wire the request body into your service? Does your repository's SQL actually return what you think it returns against a real schema? Does a unique constraint violation get translated into a proper 409 instead of an unhandled 500? Does your Pydantic response model actually serialize the ORM object correctly? None of that is visible to a unit test that mocks the database away. Integration testing is where you find out whether the pieces you unit-tested actually fit together — using a real (but disposable) database and a real HTTP client hitting your real FastAPI app, in-process.

## Core Concept

An **integration test** verifies that two or more components of your system work correctly together — most commonly, in an API context: your route handler, your dependency injection, your service layer, and a real database, all exercised through an actual HTTP-shaped request/response cycle. The key difference from a unit test is what's *real*:

| | Unit test | Integration test |
|---|---|---|
| Database | mocked/faked | real (test instance) |
| HTTP layer | not involved | real (`TestClient` / `httpx.AsyncClient`) |
| Speed | milliseconds | tens to hundreds of milliseconds |
| Scope | one function | one endpoint's full request lifecycle |
| Catches | logic bugs | wiring bugs, serialization bugs, query bugs, status-code bugs |

Crucially, "real database" does not mean "your production database" or even "a shared staging database." It means an isolated, disposable test database — often a fresh PostgreSQL instance in a container, or at minimum a dedicated test schema — that your test suite fully controls, seeds, and tears down. `test-databases.md`, an upcoming chapter, covers strategies for provisioning that database; this chapter assumes you have one and focuses on how to test *against* it correctly.

## Mental Model

If a unit test is testing one machine off the assembly line, an integration test is running a short, controlled section of the assembly line together — the intake belt, the tax-calculation machine, and the packaging station — with a stand-in product, to confirm they hand work to each other correctly. You're not running the entire factory (that's `end-to-end-testing.md`'s job, which might include a real browser, a real payment provider sandbox, and multiple real services talking to each other). You're checking that *your* API process, when it receives an HTTP request, correctly talks to *your* database and produces the right HTTP response — nothing external, but nothing faked internally either.

## How It Works

For a FastAPI application, an integration test typically does the following:

1. **Spin up a test database.** Either a fresh schema in a real PostgreSQL instance, or a throwaway container started for the test run (see [PostgreSQL Integration](../04-databases-and-apis/README.md)).
2. **Run migrations** against that test database so its schema matches what production would have (see the migrations chapter in [Part 4](../04-databases-and-apis/README.md)).
3. **Override the app's database dependency** so that, inside the test process, your FastAPI app's `Depends(get_db)` (or equivalent) resolves to a session pointed at the *test* database instead of production — FastAPI's `app.dependency_overrides` dict exists exactly for this.
4. **Instantiate a test client** — `fastapi.testclient.TestClient` for synchronous-style tests (it drives the app in-process, no real network socket), or `httpx.AsyncClient` with `ASGITransport` for genuinely async test code, paired with `pytest-asyncio`.
5. **Seed any fixture data** the test needs (a user, a product) directly through the ORM or SQL, not through the API itself, so the test doesn't depend on other endpoints working.
6. **Make the HTTP call** against the app and assert on the full response: status code, headers, and body.
7. **Tear down** — roll back the transaction, or drop/recreate the schema, so the next test starts from a clean, known state. This isolation step is the single most important mechanic in this chapter — skip it, and your suite becomes flaky under any kind of parallel or repeated execution.

## Architecture

```mermaid
flowchart TB
    subgraph TestProcess["pytest process"]
        Fixture["pytest fixture:\nsets up test DB session\n+ dependency override"]
        Client["TestClient / httpx.AsyncClient"]
        App["FastAPI app\n(real routes, real services)"]
        Fixture --> App
        Client -->|"HTTP-shaped call, in-process"| App
    end
    App -->|"real SQL"| TestDB[("Test PostgreSQL\ndisposable schema/container")]
    TestDB -.->|"rollback / drop after each test"| Teardown["Teardown"]
```

```mermaid
sequenceDiagram
    participant T as Test function
    participant C as TestClient
    participant A as FastAPI app
    participant D as Test DB

    T->>D: seed fixture data (e.g. create user)
    T->>C: POST /orders {...}
    C->>A: in-process ASGI call
    A->>D: INSERT / SELECT (real SQL)
    D-->>A: rows
    A-->>C: HTTP response (status + JSON)
    C-->>T: assert status_code, assert body
    T->>D: rollback/teardown
```

## Request / Response Example

```http
POST /orders HTTP/1.1
Content-Type: application/json
Authorization: Bearer <test-token>

{ "product_id": 42, "quantity": 2 }
```

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /orders/1001

{ "id": 1001, "product_id": 42, "quantity": 2, "status": "pending", "total_cents": 2400 }
```

```python
def test_create_order_persists_to_database(client, seeded_product):
    response = client.post("/orders", json={"product_id": seeded_product.id, "quantity": 2})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["total_cents"] == seeded_product.price_cents * 2

    # This is what makes it an integration test rather than a unit test:
    # we go check the *real* database row was actually written correctly,
    # not just that the HTTP response looked right.
    order_in_db = db_session.get(Order, body["id"])
    assert order_in_db is not None
    assert order_in_db.quantity == 2
```

## Code Example

```python
# conftest.py — shared pytest fixtures for the integration test suite.
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import Product

TEST_DATABASE_URL = "postgresql+psycopg://test_user:test_pass@localhost:5433/app_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Runs once per test session: build the schema fresh against the
    # disposable test database. Never point this at production.
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    # A fresh transaction per test, rolled back afterwards — this is the
    # isolation mechanism that keeps tests from leaking state into each other.
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()  # undo everything this test did, including commits
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    # Swap the app's real DB dependency for our test session, scoped to this test.
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()  # always clean up overrides between tests


@pytest.fixture()
def seeded_product(db_session):
    product = Product(name="Widget", price_cents=1200, stock=10)
    db_session.add(product)
    db_session.flush()  # get product.id without committing
    return product
```

```python
# test_orders_integration.py
import pytest


def test_create_order_returns_201_and_correct_total(client, seeded_product):
    response = client.post(
        "/orders", json={"product_id": seeded_product.id, "quantity": 2}
    )
    assert response.status_code == 201
    assert response.json()["total_cents"] == 2400


def test_create_order_rejects_out_of_stock_product(client, seeded_product):
    # Testing the error path, not just the happy path: quantity exceeds stock.
    response = client.post(
        "/orders", json={"product_id": seeded_product.id, "quantity": 999}
    )
    assert response.status_code == 409
    assert "insufficient stock" in response.json()["detail"].lower()


def test_create_order_for_unknown_product_returns_404(client):
    response = client.post("/orders", json={"product_id": 99999, "quantity": 1})
    assert response.status_code == 404


# Async variant, useful when the app has genuinely async route handlers
# and you want to test with the same event loop pytest-asyncio manages.
@pytest.mark.asyncio
async def test_create_order_async(async_client, seeded_product):
    response = await async_client.post(
        "/orders", json={"product_id": seeded_product.id, "quantity": 1}
    )
    assert response.status_code == 201
```

```python
# An async_client fixture, using httpx's ASGITransport to call the app
# in-process without a real network socket — needed for pytest-asyncio tests.
import httpx


@pytest.fixture()
async def async_client(db_session):
    def override_get_db():
        yield db_session

    from app.main import app
    from app.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

## Production Considerations

- **Never point integration tests at a shared or production database.** A dedicated test database (often disposable per test run, provisioned via a container — see `test-databases.md`) is what makes the suite safe to run in parallel CI jobs and safe to run destructively (`TRUNCATE`, `DROP SCHEMA`).
- **Run real migrations, not `create_all()`, when your team wants schema parity with production.** `Base.metadata.create_all()` is convenient and fast for smaller projects, but it can silently diverge from what your actual Alembic migrations produce; larger teams often run the real migration chain against the test database instead.
- **Isolate at the transaction level when possible** — wrapping each test in a transaction that's rolled back afterward is far faster than truncating tables or recreating the schema between every test, and it scales better as the suite grows.
- **Integration tests belong in CI as a distinct, slower stage** from unit tests (see `cicd-testing-pipelines.md`) — they need a database service available, which unit tests don't.
- **Watch integration test runtime as the suite grows.** They're an order of magnitude slower than unit tests; if the suite balloons into thousands of them covering trivial logic that could've been a unit test, your CI feedback loop degrades.

## Common Mistakes

- **No isolation between tests, causing flaky, order-dependent failures.** A test that creates a user with a fixed email, followed by another test doing the same thing, fails with a unique-constraint violation only when run in a particular order — a classic symptom of missing transaction rollback or missing per-test data cleanup.
- **Seeding data through the API itself** instead of directly via the ORM/DB session, which makes tests slower and couples every test's setup to the correctness of other endpoints.
- **Asserting only on status code, not on response body or database state**, missing bugs where the endpoint returns `201` but writes the wrong values.
- **Testing only the happy path** — creating an order successfully — while never exercising conflict, not-found, and validation-failure responses, which is exactly where real users hit bugs.
- **Confusing integration tests with end-to-end tests** by reaching for a real running server, a real browser, or real third-party services (payment gateways, email providers) when an in-process `TestClient` against a test database would answer the same question faster and more reliably; save that heavier setup for `end-to-end-testing.md`.

## Best Practices

- Use `app.dependency_overrides` to swap only the database dependency (and other true I/O boundaries like external API clients) — leave the rest of the app's real wiring intact, so you're actually testing the real routing, validation, and serialization.
- Wrap each test in a transaction and roll it back afterward for speed and isolation, rather than dropping/recreating the schema per test.
- Assert on the full contract: status code, response shape, and (where relevant) the resulting database state — not just one of the three.
- Keep integration tests focused on one endpoint's behavior per test; don't chain unrelated assertions about multiple endpoints into a single test function.
- Pair every happy-path integration test with at least one for a realistic failure mode (404, 409, 422) for that same endpoint.

## AI Engineering Perspective

In an AI-backed API — say, a RAG endpoint or an agent endpoint from [Part 16](../16-rag-apis/README.md) or [Part 17](../17-ai-agents-and-mcp/README.md) — integration tests are where you verify the *plumbing* around the model call: does the endpoint correctly retrieve chunks from a real (test) vector store before constructing the prompt? Does it correctly persist a conversation to the test database? Does a malformed tool-call response from the model get translated into the right HTTP error instead of a 500? The trick is to keep the LLM call itself out of the integration test's critical path — mock or stub the model client the same way you would in a unit test, returning a fixed, realistic response, so the test remains deterministic and fast while still exercising the real database and real HTTP layer around it. Testing whether the model's actual output is *good* is a separate concern (evaluation, not integration testing) and doesn't belong in this suite.

## Exercises

**Beginner**
1. Using the fixtures above, write an integration test for a `GET /orders/{id}` endpoint that asserts a 404 when the order doesn't exist in the test database.
2. Explain, in your own words, what would go wrong if the `db_session` fixture didn't roll back its transaction after each test.

**Intermediate**
3. Write an integration test that seeds two products with different stock levels and verifies that creating an order for each returns the correct `total_cents`, using a single parametrized test (`@pytest.mark.parametrize`) instead of two near-duplicate functions.

**Advanced**
4. Adapt the fixtures to run against a PostgreSQL instance started via a container library (e.g., testcontainers-style) rather than a fixed `localhost:5433` connection string, so the test suite is self-contained and doesn't depend on a manually running database. What changes about test startup time, and how would you cache that cost across a CI run?

## Key Takeaways

- Integration tests exercise real wiring — route handler, dependency injection, and a real (disposable) test database — through an actual `TestClient`/`httpx.AsyncClient` call, unlike unit tests which mock dependencies away.
- Per-test isolation, usually via transaction rollback, is the mechanic that prevents shared-state flakiness; skipping it is the most common source of a flaky integration suite.
- Seed fixture data directly through the ORM, not through the API, and assert on both the HTTP response and the resulting database state.
- Test failure paths (404, 409, validation errors), not just the happy path — that's where most real bugs surface.
- Integration tests are slower and fewer than unit tests but faster and more numerous than the full end-to-end tests covered in `end-to-end-testing.md`.
</content>
