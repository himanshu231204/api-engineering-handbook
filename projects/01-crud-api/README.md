# Project 1 — CRUD API ("Bookshelf")

## Goal

Build a "Bookshelf" resource API — a full CRUD service for managing a personal library of books — using FastAPI, Pydantic, and an in-memory or SQLite-backed store. This is the "hello world" of the handbook: it exists to prove you can turn the theory from Parts 1–3 (HTTP fundamentals, REST design, and FastAPI project structure) into a working, well-behaved API. By the end you should be able to explain every status code your API returns, every validation rule Pydantic enforces, and every design decision in your URL scheme — not just make requests succeed.

## Builds On

- [Part 1 — API Foundations](../../docs/01-api-foundations/README.md)
- [Part 2 — REST API Design](../../docs/02-rest-api-design/README.md)
- [Part 3 — Building APIs](../../docs/03-building-apis/README.md)
- Specifically: [HTTP methods](../../docs/01-api-foundations/http-methods.md), [status codes](../../docs/01-api-foundations/status-codes.md), [CRUD design](../../docs/02-rest-api-design/crud-design.md), [pagination](../../docs/02-rest-api-design/pagination.md), [filtering and sorting](../../docs/02-rest-api-design/filtering-and-sorting.md), [request validation with Pydantic](../../docs/03-building-apis/request-validation-pydantic.md), [response models](../../docs/03-building-apis/response-models.md)

## Requirements

- Create, read, update, delete, and list "books" (title, author, ISBN, genre, published year, page count, rating).
- Full input validation: reject malformed ISBNs, negative page counts, ratings outside 0–5, empty titles.
- List endpoint supports pagination (`limit`/`offset` or cursor), filtering (by genre, author, published year range), and sorting (by title, published year, rating).
- Partial updates via `PATCH` and full replacement via `PUT` behave correctly and differently.
- Proper HTTP status codes for every outcome (200, 201, 204, 400, 404, 422, 409 for duplicate ISBN).
- Every response uses a typed Pydantic response model — no raw dicts leaking internal fields.
- Auto-generated OpenAPI docs at `/docs` are accurate and usable to explore the API without reading code.
- Idempotent `PUT` and `DELETE` (calling twice produces the same end state).

## Architecture

```mermaid
flowchart LR
    Client[HTTP Client / curl / Swagger UI] -->|JSON over HTTP| API[FastAPI App]
    API --> Router[Books Router]
    Router --> Schema[Pydantic Schemas\n(BookCreate, BookUpdate, BookRead)]
    Router --> Service[Book Service\n(business rules, uniqueness checks)]
    Service --> Repo[Book Repository]
    Repo --> DB[(SQLite / In-Memory Store)]
    API --> Docs[OpenAPI / Swagger UI at /docs]
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/books` | Create a new book. 201 + `Location` header on success, 409 if ISBN already exists. |
| GET | `/books` | List books. Query params: `limit`, `offset`, `genre`, `author`, `year_from`, `year_to`, `sort_by`, `order`. |
| GET | `/books/{book_id}` | Fetch a single book by ID. 404 if not found. |
| PUT | `/books/{book_id}` | Replace a book entirely. 404 if not found, 400 if payload is incomplete. |
| PATCH | `/books/{book_id}` | Partially update a book (only supplied fields change). |
| DELETE | `/books/{book_id}` | Delete a book. 204 on success, 204 also on repeated delete (idempotent) or 404 depending on your chosen contract — document which. |
| GET | `/health` | Liveness check for the service itself. |

## Database Schema

```sql
CREATE TABLE books (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title          TEXT NOT NULL,
    author         TEXT NOT NULL,
    isbn           TEXT UNIQUE NOT NULL,
    genre          TEXT NOT NULL,
    published_year INTEGER NOT NULL,
    page_count     INTEGER NOT NULL CHECK (page_count > 0),
    rating         NUMERIC(2,1) CHECK (rating >= 0 AND rating <= 5),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_books_genre ON books (genre);
CREATE INDEX idx_books_author ON books (author);
CREATE INDEX idx_books_published_year ON books (published_year);
```

## Suggested Folder Structure

```
01-crud-api/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       └── books.py
│   ├── schemas/
│   │   └── book.py
│   ├── services/
│   │   └── book_service.py
│   ├── repositories/
│   │   └── book_repository.py
│   ├── models/
│   │   └── book.py
│   ├── db/
│   │   └── session.py
│   └── core/
│       ├── config.py
│       └── exceptions.py
├── tests/
│   ├── test_create_book.py
│   ├── test_list_books.py
│   ├── test_update_book.py
│   └── test_delete_book.py
├── requirements.txt
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold a FastAPI project (`app/main.py`) with a `/health` endpoint and confirm `/docs` renders.
2. Define the `Book` SQLAlchemy (or SQLModel) model and a SQLite database session, per [project architecture](../../docs/03-building-apis/project-architecture.md).
3. Write Pydantic schemas: `BookCreate`, `BookUpdate` (all fields optional), and `BookRead` (the response model), applying [request validation](../../docs/03-building-apis/request-validation-pydantic.md).
4. Implement the repository layer: `create`, `get_by_id`, `get_by_isbn`, `list` (with filter/sort/paginate params), `update`, `delete`.
5. Implement the service layer that enforces business rules (ISBN uniqueness, year sanity checks) and translates repository results into HTTP-appropriate outcomes.
6. Wire up the `POST /books` route: validate, check for existing ISBN, create, return 201 with `Location` header.
7. Wire up `GET /books` with pagination, filtering, and sorting query parameters; return a typed paginated response envelope (`items`, `total`, `limit`, `offset`).
8. Wire up `GET /books/{id}`, `PUT /books/{id}`, `PATCH /books/{id}`, `DELETE /books/{id}`, each mapping domain outcomes to correct status codes per [status codes](../../docs/01-api-foundations/status-codes.md).
9. Add centralized exception handling (`RequestValidationError`, `NotFoundError`, `ConflictError`) so error responses have a consistent JSON shape.
10. Write unit tests for the service layer and integration tests (via `TestClient`) for every endpoint, including edge cases (duplicate ISBN, invalid rating, non-existent ID).
11. Add `.env`-based configuration for database URL and pagination defaults, per [environment variables](../../docs/03-building-apis/environment-variables.md).
12. Polish OpenAPI docs: descriptions, examples, and tags on every route so `/docs` is genuinely usable by a stranger.

## Advanced Improvements

- Swap SQLite for PostgreSQL and add Alembic migrations.
- Add soft deletes (`deleted_at`) instead of hard deletes, and filter them out of list results.
- Add full-text search on title/author using SQL `LIKE`/`ILIKE` or Postgres `tsvector`.
- Add ETags / `If-Match` support for optimistic concurrency control on `PUT`/`PATCH`.
- Add bulk endpoints: `POST /books/bulk` for batch creation.
- Add an `average_rating` computed field aggregated from a related `reviews` table.
- Containerize with Docker and add a `docker-compose.yml` with Postgres.

## Production Checklist

- [ ] Input validation covers every field, including boundary values (empty strings, negative numbers, future years).
- [ ] Consistent, documented error response schema across all 4xx/5xx cases.
- [ ] Pagination defaults and max page size enforced server-side (don't trust client-supplied `limit`).
- [ ] Database indexes on all filterable/sortable columns to avoid full table scans.
- [ ] Structured logging on every request (method, path, status, latency).
- [ ] Automated tests covering happy paths, validation failures, and not-found cases with CI running them on every push.
- [ ] `/health` endpoint wired into a container orchestrator's liveness probe.
- [ ] API versioned from day one (`/v1/books`) even though there's only one version.
- [ ] No secrets or DB credentials hardcoded — pulled from environment variables.
- [ ] OpenAPI schema reviewed as the actual API contract, not an afterthought.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
