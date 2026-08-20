"""
A resource-oriented API, built without a web framework, that demonstrates
REST *design* decisions in isolation from any framework's conveniences.

This is deliberately NOT FastAPI (see ../fastapi-crud for that). The point
here is to show that things like "pagination shape" or "path parameters" are
design choices you make, not something a framework gives you for free.

Resource: articles, with a nested sub-resource: comments.

    GET    /articles                 list (paginated, filterable, sortable)
    POST   /articles                 create
    GET    /articles/{id}            read one
    PATCH  /articles/{id}            partial update
    DELETE /articles/{id}            delete
    GET    /articles/{id}/comments   list a nested collection

Run it:
    python app.py

Then:
    curl "http://127.0.0.1:8000/articles"
    curl "http://127.0.0.1:8000/articles?limit=2&offset=1"
    curl "http://127.0.0.1:8000/articles?author=ada&sort=-created_at"
    curl "http://127.0.0.1:8000/articles/1"
    curl "http://127.0.0.1:8000/articles/1/comments"
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import count
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8000

# ---------------------------------------------------------------------------
# "Database" -- an in-memory list, seeded with a few rows. Not the point of
# this example; see examples/fastapi-crud for real persistence.
# ---------------------------------------------------------------------------

_id_seq = count(1)

ARTICLES: dict[int, dict] = {}
COMMENTS: dict[int, list[dict]] = {}


def _seed() -> None:
    seed_data = [
        {"title": "Understanding REST", "author": "ada", "body": "Resources, not RPCs."},
        {"title": "Pagination Done Right", "author": "grace", "body": "Cursor vs offset."},
        {"title": "Naming Your Endpoints", "author": "ada", "body": "Nouns, plural, lowercase."},
    ]
    for row in seed_data:
        article_id = next(_id_seq)
        now = datetime.now(timezone.utc).isoformat()
        ARTICLES[article_id] = {
            "id": article_id,
            "title": row["title"],
            "author": row["author"],
            "body": row["body"],
            "created_at": now,
        }
        COMMENTS[article_id] = [
            {"id": 1, "article_id": article_id, "text": f"Great post, {row['author']}!"},
        ]


_seed()

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

# Resource naming convention: plural nouns, lowercase, no verbs in the URL.
#   /articles            (collection)
#   /articles/{id}        (member -- a path parameter, not a query parameter,
#                          because it identifies *which* resource, not how
#                          to filter/shape a collection)
#   /articles/{id}/comments  (a nested collection scoped to its parent)
ARTICLE_COLLECTION = re.compile(r"^/articles/?$")
ARTICLE_MEMBER = re.compile(r"^/articles/(?P<id>\d+)/?$")
ARTICLE_COMMENTS = re.compile(r"^/articles/(?P<id>\d+)/comments/?$")

MAX_LIMIT = 50
DEFAULT_LIMIT = 10


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "RestApiDesignExample/1.0"

    # -- dispatch -----------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)

        if ARTICLE_COLLECTION.match(path):
            self._list_articles(query)
        elif (m := ARTICLE_MEMBER.match(path)):
            self._get_article(int(m.group("id")))
        elif (m := ARTICLE_COMMENTS.match(path)):
            self._list_comments(int(m.group("id")), query)
        else:
            self._error(404, "not_found", f"No route for GET {path}")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if ARTICLE_COLLECTION.match(path):
            self._create_article()
        else:
            self._error(404, "not_found", f"No route for POST {path}")

    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if (m := ARTICLE_MEMBER.match(path)):
            self._update_article(int(m.group("id")))
        else:
            self._error(404, "not_found", f"No route for PATCH {path}")

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if (m := ARTICLE_MEMBER.match(path)):
            self._delete_article(int(m.group("id")))
        else:
            self._error(404, "not_found", f"No route for DELETE {path}")

    # -- handlers -------------------------------------------------------

    def _list_articles(self, query: dict[str, list[str]]) -> None:
        rows = list(ARTICLES.values())

        # Filtering: plain query parameters, one per filterable field.
        # /articles?author=ada
        if "author" in query:
            author = query["author"][0]
            rows = [r for r in rows if r["author"] == author]

        # Sorting: a `sort` query parameter; a leading "-" means descending.
        # /articles?sort=-created_at  or  /articles?sort=title
        if "sort" in query:
            sort_field = query["sort"][0]
            descending = sort_field.startswith("-")
            field = sort_field.lstrip("-")
            if field in ("title", "author", "created_at", "id"):
                rows.sort(key=lambda r: r[field], reverse=descending)

        # Pagination: offset/limit query parameters with sane defaults and
        # a hard upper bound so a client can't request the entire table.
        try:
            limit = min(int(query.get("limit", [DEFAULT_LIMIT])[0]), MAX_LIMIT)
            offset = max(int(query.get("offset", [0])[0]), 0)
        except ValueError:
            self._error(400, "invalid_query_parameter", "limit/offset must be integers")
            return

        total = len(rows)
        page = rows[offset : offset + limit]

        # Response shape: results + pagination metadata, so a client never
        # has to guess whether there's more data or infer total count from
        # a bare array's length.
        self._json(
            200,
            {
                "results": page,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "next_offset": offset + limit if offset + limit < total else None,
                },
            },
        )

    def _get_article(self, article_id: int) -> None:
        article = ARTICLES.get(article_id)
        if article is None:
            self._error(404, "not_found", f"No article with id {article_id}")
            return
        self._json(200, article)

    def _list_comments(self, article_id: int, query: dict[str, list[str]]) -> None:
        if article_id not in ARTICLES:
            self._error(404, "not_found", f"No article with id {article_id}")
            return
        comments = COMMENTS.get(article_id, [])
        self._json(200, {"results": comments, "pagination": {"total": len(comments)}})

    def _create_article(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        missing = [f for f in ("title", "author", "body") if f not in body]
        if missing:
            self._error(422, "validation_error", f"Missing fields: {', '.join(missing)}")
            return

        article_id = next(_id_seq)
        article = {
            "id": article_id,
            "title": body["title"],
            "author": body["author"],
            "body": body["body"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        ARTICLES[article_id] = article
        COMMENTS[article_id] = []

        # 201 Created + Location header pointing at the new resource's URL --
        # this is how a REST API tells the client "here's where to find it".
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Location", f"/articles/{article_id}")
        body_bytes = json.dumps(article, indent=2).encode("utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def _update_article(self, article_id: int) -> None:
        article = ARTICLES.get(article_id)
        if article is None:
            self._error(404, "not_found", f"No article with id {article_id}")
            return
        body = self._read_json_body()
        if body is None:
            return
        # PATCH = partial update: only overwrite fields the client sent.
        for field in ("title", "author", "body"):
            if field in body:
                article[field] = body[field]
        self._json(200, article)

    def _delete_article(self, article_id: int) -> None:
        if article_id not in ARTICLES:
            self._error(404, "not_found", f"No article with id {article_id}")
            return
        del ARTICLES[article_id]
        COMMENTS.pop(article_id, None)
        # 204 No Content: successful delete, nothing meaningful to return.
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # -- helpers ----------------------------------------------------------

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        if not raw:
            self._error(400, "invalid_body", "Request body must be JSON")
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            self._error(400, "invalid_body", "Request body is not valid JSON")
            return None
        if not isinstance(data, dict):
            self._error(400, "invalid_body", "Request body must be a JSON object")
            return None
        return data

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, code: str, message: str) -> None:
        # Consistent error shape across every endpoint -- a client should
        # never have to guess where the error message lives in the body.
        self._json(status, {"error": {"code": code, "message": message}})

    def log_message(self, fmt: str, *args) -> None:
        print(f"[app] {self.address_string()} - {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
