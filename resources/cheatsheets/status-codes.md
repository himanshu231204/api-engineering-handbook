# HTTP Status Codes Cheatsheet

For the full explanation, see [Status Codes](../../docs/01-api-foundations/status-codes.md).

## 2xx — Success

| Code | Meaning | When to use |
|---|---|---|
| `200 OK` | Generic success | Default success response with a body (`GET`, `PUT`, `PATCH`, sometimes `POST`) |
| `201 Created` | Resource created | Successful `POST` that created a resource — include `Location` header |
| `202 Accepted` | Accepted for async processing | Request queued but not yet complete (background job, webhook received) |
| `204 No Content` | Success, no body | Successful `DELETE`, or `PUT`/`PATCH` with nothing to return |

## 3xx — Redirection

| Code | Meaning | When to use |
|---|---|---|
| `301 Moved Permanently` | Resource permanently moved | URL structure changed permanently, update bookmarks/clients |
| `302 Found` | Temporary redirect | Temporary redirect, method may change on redirect (legacy behavior) |
| `304 Not Modified` | Cached version is still valid | Client sent `If-None-Match`/`If-Modified-Since` and nothing changed |
| `307 Temporary Redirect` | Temporary redirect, method preserved | Like 302 but guarantees method/body are resent unchanged |

## 4xx — Client Errors

| Code | Meaning | When to use |
|---|---|---|
| `400 Bad Request` | Malformed request | Invalid JSON, failed validation, missing required field |
| `401 Unauthorized` | Not authenticated | Missing/invalid credentials — client should (re)authenticate |
| `403 Forbidden` | Authenticated but not allowed | Valid credentials, but caller lacks permission for this resource |
| `404 Not Found` | Resource doesn't exist | No resource at this URL (or hidden for security reasons) |
| `405 Method Not Allowed` | Method not supported here | e.g. `DELETE` on a read-only endpoint — include `Allow` header |
| `409 Conflict` | Request conflicts with current state | Duplicate unique key, version/optimistic-lock conflict |
| `410 Gone` | Resource permanently removed | Was here, deliberately deleted, not coming back |
| `422 Unprocessable Entity` | Syntactically valid but semantically invalid | Well-formed JSON that fails business-rule validation |
| `429 Too Many Requests` | Rate limit exceeded | Include `Retry-After` header |

## 5xx — Server Errors

| Code | Meaning | When to use |
|---|---|---|
| `500 Internal Server Error` | Unhandled server-side failure | Unexpected exception — never leak stack traces to the client |
| `502 Bad Gateway` | Upstream returned an invalid response | Gateway/proxy got garbage from the backend it called |
| `503 Service Unavailable` | Server temporarily can't handle requests | Overloaded, in maintenance, or circuit breaker is open — include `Retry-After` |
| `504 Gateway Timeout` | Upstream took too long | Gateway/proxy's call to the backend timed out |

## Quick decision guide

- Validation failure on input → `400` (malformed) or `422` (well-formed but invalid).
- Client didn't prove who they are → `401`. Client proved who they are but can't do this → `403`.
- Don't want to reveal a resource exists to an unauthorized caller → return `404` instead of `403`.
- Retryable failure (rate limit, transient overload) → `429`/`503` with a `Retry-After` header.
- Never invent custom codes outside the registered range — use the closest standard code plus a structured error body for details.
