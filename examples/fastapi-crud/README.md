# FastAPI CRUD Service — Production-Structured

Accompanies [Part 3 — Building APIs](../../docs/03-building-apis/README.md). Every chapter in
that part shows up here as real, runnable code:
[FastAPI Fundamentals](../../docs/03-building-apis/fastapi-fundamentals.md),
[Request Validation with Pydantic](../../docs/03-building-apis/request-validation-pydantic.md),
[Response Models](../../docs/03-building-apis/response-models.md),
[Dependency Injection](../../docs/03-building-apis/dependency-injection.md),
[Middleware](../../docs/03-building-apis/middleware.md),
[Exception Handling](../../docs/03-building-apis/exception-handling.md),
[Project Architecture](../../docs/03-building-apis/project-architecture.md),
[Environment Variables](../../docs/03-building-apis/environment-variables.md),
[Configuration Management](../../docs/03-building-apis/configuration-management.md), and
[API Documentation with OpenAPI](../../docs/03-building-apis/openapi-documentation.md).

It also uses the repository pattern (a Part 4 topic — see the
[Databases & APIs](../../docs/04-databases-and-apis/README.md) index, currently planned), one
chapter early, because a "real" project layout needs a persistence boundary from day one.

## What this demonstrates

A complete `Task` CRUD API, structured the way a real FastAPI service is structured —
not a single-file toy:

```text
app/
  main.py                     # app factory: middleware, exception handlers, routers, lifespan
  core/
    config.py                 # Pydantic Settings, loaded from env vars / .env
    database.py                # SQLAlchemy engine, session factory, get_db dependency
    exceptions.py              # domain-level exceptions (HTTP-agnostic)
  models/
    task.py                    # SQLAlchemy ORM model
  schemas/
    task.py                    # Pydantic v2 request/response models
  repositories/
    task_repository.py         # all DB access lives here, behind a small interface
  routers/
    tasks.py                   # /tasks endpoints -- thin, delegate to the repository
tests/
  test_tasks.py                 # smoke tests using TestClient + an isolated in-memory DB
```

Specifically, look for:

- **Dependency injection chains**: `get_db` → `get_task_repository` → route handler.
  FastAPI resolves the whole chain per request (`app/routers/tasks.py`).
- **Pydantic v2 schemas** separate from the SQLAlchemy model, with a real PATCH semantics
  (`TaskUpdate` uses `exclude_unset=True` so omitted fields aren't clobbered).
- **Middleware**: a custom `X-Process-Time-Ms` timing middleware plus CORS
  (`app/main.py`).
- **Centralized exception handling**: repositories raise `TaskNotFoundError`; one handler
  in `main.py` turns that into a 404 with a consistent error shape — route handlers never
  write `try/except` for this.
- **Configuration via `pydantic-settings`**, cached with `lru_cache` so `.env` is parsed
  once per process (`app/core/config.py`).
- **SQLite via SQLAlchemy 2.0** (typed `Mapped[...]` columns) so the example runs with no
  external database — point `DATABASE_URL` at Postgres and nothing else changes.
- **Auto-generated OpenAPI docs** — FastAPI gives you `/docs` and `/openapi.json` for
  free from the same type hints and Pydantic models used for validation.

## Prerequisites

- Python 3.11+

## How to run it

```bash
cd examples/fastapi-crud
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env   # optional -- sensible defaults work with no .env at all

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive Swagger UI, or try it with curl:

```bash
# Create
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Ship the handbook", "priority": "high"}'

# List (paginated)
curl "http://127.0.0.1:8000/tasks?limit=5&offset=0"

# Filter
curl "http://127.0.0.1:8000/tasks?completed=false"

# Read one
curl http://127.0.0.1:8000/tasks/1

# Partial update
curl -X PATCH http://127.0.0.1:8000/tasks/1 -H "Content-Type: application/json" -d '{"completed": true}'

# Delete
curl -i -X DELETE http://127.0.0.1:8000/tasks/1

# Watch the custom middleware header on any request
curl -i http://127.0.0.1:8000/health
```

Run the tests:

```bash
pytest
```

## Things to try

1. **Trigger the validation layer.** POST a task with `"title": ""` or `"priority":
   "urgent"` (not a valid enum value) and look at the 422 response body — that structured
   error comes entirely from Pydantic, with zero code written for it.
2. **Break PATCH on purpose.** In `TaskRepository.update`, change
   `exclude_unset=True` to `exclude_unset=False` and PATCH just `{"completed": true}` —
   watch every other field silently reset to its schema default. This is the bug that
   `exclude_unset` exists to prevent.
3. **Swap SQLite for Postgres.** Change `DATABASE_URL` in `.env` to a Postgres URL and
   run `pip install psycopg[binary]` — nothing else in `app/` needs to change, which is
   the point of putting persistence behind `TaskRepository` and `get_db`.
4. **Add a new domain exception.** Add a `DuplicateTitleError`, raise it from
   `TaskRepository.create` when a title already exists, and register a second
   `@app.exception_handler` for it in `main.py` — see how cleanly a new error case slots
   into the existing pattern.
