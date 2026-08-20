# HTTP Methods Cheatsheet

For the full explanation, see [HTTP Methods](../../docs/01-api-foundations/http-methods.md).

| Method | Safe? | Idempotent? | Has Request Body? | Has Response Body? | Typical Use |
|---|---|---|---|---|---|
| `GET` | Yes | Yes | No (by convention) | Yes | Retrieve a resource or collection, no side effects |
| `POST` | No | No | Yes | Yes | Create a new resource, trigger a non-idempotent action (e.g. "send email", "charge card") |
| `PUT` | No | Yes | Yes | Optional | Replace a resource entirely with the given representation |
| `PATCH` | No | No (but *can* be designed to be) | Yes | Optional | Partially update a resource (a subset of fields) |
| `DELETE` | No | Yes | Optional | Optional | Remove a resource |
| `HEAD` | Yes | Yes | No | No (headers only) | Same as `GET` but headers only — check existence, size, cache validity |
| `OPTIONS` | Yes | Yes | No | Yes (allowed methods/CORS info) | Discover allowed methods/CORS preflight |

## Definitions in one line

- **Safe** — the method must not change server state (read-only). `GET`, `HEAD`, `OPTIONS` are safe.
- **Idempotent** — calling it once or N times produces the same server state. `GET`, `PUT`, `DELETE` are idempotent; `POST` generally is not; `PATCH` is idempotent only if you design it that way (e.g. "set status to `active`" is idempotent, "increment counter by 1" is not).

## Quick decision guide

- Creating a new resource where the server assigns the ID → `POST`.
- Creating/replacing a resource at a client-known URL (e.g. `PUT /users/42`) → `PUT`.
- Updating a few fields without sending the whole resource → `PATCH`.
- Need retry-safety on an unreliable network → prefer `PUT`/`DELETE` over `POST`, or add an idempotency key to `POST`.
- Checking if a resource exists without downloading it → `HEAD`.
- Browser is about to send a cross-origin `PUT`/`DELETE`/custom-header request → expect a preflight `OPTIONS`.

## Common mistakes

- Using `GET` with a request body (many servers/proxies drop it — don't rely on it).
- Treating `PATCH` as automatically idempotent — verify your own semantics.
- Using `POST` for "get search results with a huge query" purely to sidestep URL-length limits without acknowledging it breaks caching/idempotency assumptions.
- Returning `200 OK` for a `DELETE` of a resource that no longer exists — decide deliberately between `204 No Content` and `404 Not Found`.
