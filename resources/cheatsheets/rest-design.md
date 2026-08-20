# REST API Design Cheatsheet

For the full explanation, see [REST API Design](../../docs/02-rest-api-design/README.md).

## Naming conventions

| Rule | Good | Bad |
|---|---|---|
| Nouns, not verbs, in the path | `POST /orders` | `POST /createOrder` |
| Plural collection names | `/users`, `/orders` | `/user`, `/order` |
| Nested resources for ownership | `/users/42/orders` | `/getOrdersForUser?id=42` |
| lowercase, hyphen-separated paths | `/order-items` | `/orderItems`, `/Order_Items` |
| Use the method to express the action | `DELETE /orders/42` | `POST /orders/42/delete` |
| Query params for filtering, not paths | `/orders?status=paid` | `/orders/paid` |

## Pagination styles

| Style | How it works | Pros | Cons | Best for |
|---|---|---|---|---|
| **Offset/limit** | `?offset=40&limit=20` | Simple, supports "jump to page N" | Slow on large offsets, unstable if rows are inserted/deleted mid-pagination | Small-medium datasets, admin UIs |
| **Page number** | `?page=3&per_page=20` | Human-friendly, simple | Same instability issue as offset, still O(offset) in the DB | User-facing paged UIs |
| **Cursor-based** | `?cursor=eyJpZCI6NDJ9&limit=20` (opaque cursor, usually encoding last-seen sort key) | Stable under concurrent writes, O(1) per page regardless of depth | No "jump to page N", cursor must be generated/parsed by the server | Infinite scroll, high-write-rate large tables, public APIs |
| **Keyset (seek)** | `?after_id=1042&limit=20` (explicit last-seen key) | Same performance benefits as cursor, human-readable | Requires a strictly ordered, indexed column | High-throughput APIs with a natural sort key (e.g. `created_at`, `id`) |

## Versioning approaches

| Approach | Example | Pros | Cons |
|---|---|---|---|
| URI path | `/v1/orders` | Explicit, cacheable, easy to route | "Not RESTful" purists object; URL changes across versions |
| Query parameter | `/orders?version=1` | Easy to default | Easy to forget, less visible, harder to route at gateway level |
| Custom header | `X-API-Version: 1` | Keeps URLs clean | Invisible in browser/logs, easy to omit by accident |
| Accept header (content negotiation) | `Accept: application/vnd.myapi.v1+json` | "Proper" REST/HTTP way | Least discoverable, harder for API consumers to work with |

Most production APIs use **URI path versioning** for discoverability, even though it's the least "pure REST."

## Quick dos and don'ts

**Do**
- Return consistent, predictable JSON shapes (envelope or not — pick one and stick to it).
- Use plural nouns and nested resources to express relationships.
- Support filtering, sorting, and pagination on every collection endpoint.
- Version your API from day one, even if it's just `/v1`.
- Return the created resource (with its new ID/URL) from a `201 Created` response.
- Document your contract with OpenAPI and keep it in sync with the code.

**Don't**
- Don't put verbs in URLs (`/getUser`, `/deleteOrder`).
- Don't expose your database schema 1:1 as your API — design the contract deliberately.
- Don't return `200 OK` for errors with an error message in the body — use real status codes.
- Don't break backward compatibility within a version — add fields, don't remove/rename them.
- Don't let pagination be unbounded — always enforce a max `limit`.
- Don't mix pagination styles across endpoints in the same API.
