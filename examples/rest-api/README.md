# REST API Design — Resource Naming, Path/Query Params, Pagination

Accompanies [Part 2 — REST API Design](../../docs/02-rest-api-design/README.md), especially
[Resources and Endpoints](../../docs/02-rest-api-design/resources-and-endpoints.md),
[Path Parameters](../../docs/02-rest-api-design/path-parameters.md),
[Query Parameters](../../docs/02-rest-api-design/query-parameters.md),
[CRUD Design](../../docs/02-rest-api-design/crud-design.md), and
[Pagination](../../docs/02-rest-api-design/pagination.md).

## What this demonstrates

This is a **design** exercise, not a framework exercise — it's deliberately built on
`http.server` instead of FastAPI (that's [`../fastapi-crud`](../fastapi-crud/)) so that
the design decisions are visible on their own, not buried under a framework's routing
sugar.

It implements a single resource, `articles`, plus a nested sub-resource, `comments`, and
shows:

- **Resource naming**: plural nouns (`/articles`, not `/getArticle` or `/article`),
  lowercase, no verbs in the URL — the HTTP method is the verb.
- **Path parameters** for identifying *which* resource (`/articles/{id}`).
- **Query parameters** for filtering, sorting, and paginating a *collection*
  (`/articles?author=ada&sort=-created_at&limit=10&offset=0`) — never used to identify a
  single resource.
- **A consistent pagination response shape**: every list endpoint returns
  `{"results": [...], "pagination": {"total", "limit", "offset", "next_offset"}}`
  instead of a bare array, so a client never has to guess whether there's more data.
- **Correct status codes**: `201 Created` with a `Location` header on create,
  `204 No Content` on delete, `404` for missing resources, `422` for validation errors,
  `400` for malformed input.
- **A consistent error shape**: `{"error": {"code": ..., "message": ...}}` on every
  failure path.
- **Nested collections**: `/articles/{id}/comments` scopes a sub-resource under its
  parent instead of a flat `/comments?article_id=1`.

## Prerequisites

- Python 3.11+
- `curl` (or any HTTP client) to try it out — no third-party Python packages needed.

## How to run it

```bash
cd examples/rest-api
python app.py
# Serving on http://127.0.0.1:8000
```

In another terminal:

```bash
# List (default page: limit=10, offset=0)
curl "http://127.0.0.1:8000/articles"

# Filter + sort + paginate
curl "http://127.0.0.1:8000/articles?author=ada&sort=-created_at&limit=1"

# Read one (path parameter)
curl "http://127.0.0.1:8000/articles/1"

# Create — note the 201 + Location header
curl -i -X POST "http://127.0.0.1:8000/articles" \
  -d '{"title": "New Post", "author": "lin", "body": "hello"}'

# Partial update
curl -X PATCH "http://127.0.0.1:8000/articles/1" -d '{"title": "Updated Title"}'

# Delete — note the 204 with an empty body
curl -i -X DELETE "http://127.0.0.1:8000/articles/2"

# Nested collection
curl "http://127.0.0.1:8000/articles/1/comments"

# 404 with the consistent error shape
curl "http://127.0.0.1:8000/articles/999"
```

## Things to try

1. **Add a second filter.** Add a `title` substring filter (e.g.
   `?title_contains=REST`) to `_list_articles` and decide: should combining multiple
   filters be AND or OR? Most REST APIs choose AND — see if you agree once you've
   implemented it.
2. **Cap the page size differently.** `MAX_LIMIT` currently silently clamps an
   over-large `limit`. Change it to return a `400` instead, and think about which
   behavior is friendlier to API consumers (hint: what does a client do differently in
   each case?).
3. **Compare this to `examples/fastapi-crud`.** Once you've read that example, come
   back here and count how many lines of *this* file exist purely to do things FastAPI +
   Pydantic give you automatically (query parsing, validation, JSON encoding, status code
   handling). That gap is what a framework actually buys you.
