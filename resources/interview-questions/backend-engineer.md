# Backend Engineer Interview Questions

Questions drawn from Parts 1–13 of the handbook (HTTP fundamentals through API testing). Each includes a brief model answer or the key points an interviewer is listening for.

## Fundamentals & HTTP

**1. What's the difference between `PUT` and `PATCH`?**
`PUT` replaces a resource entirely with the representation you send — any field you omit is effectively cleared/reset. `PATCH` applies a partial update, sending only the fields that changed. `PUT` is idempotent by definition; `PATCH` is idempotent only if you design it that way (e.g. "set field to X" vs. "increment field by 1").

**2. Explain the difference between `401 Unauthorized` and `403 Forbidden`.**
`401` means the request lacks valid authentication — the server doesn't know who you are (or your credentials are invalid/expired). `403` means the server knows who you are but you don't have permission to perform this action on this resource. A common mistake is returning `401` when you mean `403`, or vice versa.

**3. Why is `GET` supposed to be safe and idempotent, and what breaks if you don't honor that?**
Safe means no server-side side effects; idempotent means repeating it produces the same result. Browsers, proxies, and CDNs assume `GET` is safe/idempotent — they'll prefetch, retry, and cache `GET` requests automatically. A `GET /delete-account?id=5` violates this contract and can get accidentally triggered by a crawler or browser prefetch.

**4. What is idempotency, and why does it matter for a payment API specifically?**
An idempotent operation produces the same result no matter how many times it's applied. For payments, network failures mean a client can't always tell if a request succeeded — a naive retry of `POST /charge` could double-charge a customer. The fix is an idempotency key: the client generates a unique key per logical operation, and the server deduplicates requests with the same key within a time window.

## REST API Design

**5. How would you design pagination for an endpoint returning millions of rows that are frequently inserted?**
Offset-based pagination degrades because `OFFSET 500000` still scans and discards 500,000 rows, and results shift if rows are inserted mid-pagination. Use cursor/keyset pagination instead — encode the last-seen sort key (e.g. `id` or `created_at`) as an opaque cursor, and query `WHERE id > :cursor ORDER BY id LIMIT :n`, which uses an index and stays stable under concurrent writes.

**6. What goes into a good API versioning strategy?**
Decide on a versioning scheme up front (URI path is the most common and discoverable: `/v1/orders`). Never break a published version — only add fields/endpoints, never remove or repurpose existing ones. Deprecate old versions with a clear timeline and `Sunset`/`Deprecation` headers, and communicate migration paths before removal.

**7. Design the endpoints for a simple blog API with posts and comments.**
`GET /posts`, `POST /posts`, `GET /posts/{id}`, `PATCH /posts/{id}`, `DELETE /posts/{id}` for posts; nest comments under their post for creation/listing (`GET /posts/{id}/comments`, `POST /posts/{id}/comments`) but give comments their own top-level identity for direct access/modification (`GET /comments/{id}`, `DELETE /comments/{id}`) since a comment's identity doesn't depend on always being addressed through its post.

## Building APIs

**8. What does dependency injection buy you in a FastAPI (or similar) application?**
It decouples a route handler from how its dependencies (DB sessions, current user, config) are constructed, making handlers testable (swap in mocks/fakes) and letting shared logic (auth checks, DB session lifecycle) live in one reusable place instead of being duplicated in every handler.

**9. Where should validation happen in a layered API, and why not just validate in the database?**
Validate as early as possible — at the request boundary (e.g. Pydantic models) — so bad input is rejected before it triggers business logic, DB queries, or side effects, and so the client gets a fast, specific `400`/`422` error. Database constraints (`NOT NULL`, `UNIQUE`, foreign keys) are still valuable as a last line of defense against bugs elsewhere in the code, not a substitute for input validation.

**10. What's the value of a project layout that separates routers, services, and repositories?**
It isolates concerns: routers handle HTTP (parsing requests, status codes), services hold business logic, repositories handle data access. This makes each layer independently testable, lets you swap the data layer (e.g. Postgres → a different store) without touching business logic, and prevents HTTP-specific concerns (headers, status codes) from leaking into business logic.

## Databases

**11. What's the N+1 query problem and how do you fix it?**
It happens when you fetch a list of N records, then issue one additional query per record to fetch related data (e.g. fetching 50 orders, then querying each order's customer separately = 51 queries). Fix it with eager loading (SQL `JOIN`, or ORM constructs like `joinedload`/`select_related`) to fetch everything in one or two queries instead.

**12. Why do you need a connection pool instead of opening a new DB connection per request?**
Opening a TCP connection and authenticating with the database has real latency and resource cost (memory, file descriptors) on both client and server. A connection pool keeps a set of live connections ready to reuse, dramatically reducing per-request overhead and preventing you from exhausting the database's max-connections limit under load.

**13. What's a database transaction, and what does ACID mean?**
A transaction groups multiple operations so they either all succeed or all fail together. ACID: **Atomicity** (all-or-nothing), **Consistency** (moves the DB from one valid state to another), **Isolation** (concurrent transactions don't see each other's uncommitted changes), **Durability** (once committed, survives crashes).

**14. Why use database migrations instead of manually altering schema in production?**
Migrations are version-controlled, repeatable, and reviewable — every environment (dev, staging, prod) applies the exact same sequence of schema changes, and you can roll back a bad change. Manual `ALTER TABLE` in a prod console is unauditable and easy to apply inconsistently across environments.

## Authentication & Authorization

**15. Walk through what happens, step by step, when a user logs in with JWT-based auth.**
Client sends credentials to `/login`. Server verifies them, then issues a signed JWT access token (short-lived) and a refresh token (long-lived, often stored more securely). Client stores tokens and sends the access token as `Authorization: Bearer <token>` on subsequent requests. Server verifies the JWT's signature and expiry (no DB lookup needed) to authorize each request. When the access token expires, the client uses the refresh token to get a new one.

**16. Why can't you easily revoke a JWT before it expires?**
JWTs are stateless by design — the server verifies them by checking the signature, not by looking them up in a store. There's no built-in "delete this token" operation. Mitigations: keep access tokens short-lived, maintain a blocklist/deny-list for compromised tokens (reintroducing some statefulness), or use opaque tokens with server-side lookup when instant revocation matters more than statelessness.

**17. Explain RBAC vs ABAC and when you'd choose one over the other.**
RBAC assigns permissions to roles and users to roles (`admin`, `editor`) — simple, auditable, good for a small number of clear-cut permission tiers. ABAC evaluates permissions based on attributes of the user, resource, action, and context (e.g. "user can edit if they're in the same department as the resource owner AND it's before the resource's lock date") — more flexible for fine-grained, contextual rules, at the cost of complexity.

## Reliability

**18. A downstream service you depend on starts timing out intermittently. What do you put in place?**
Set an aggressive but reasonable timeout so you're not blocked indefinitely. Add retries with exponential backoff and jitter for transient failures, but cap total attempts/time. Wrap the dependency in a circuit breaker so sustained failures fail fast instead of exhausting your own resources. Have a fallback (cached data, degraded response) for when the circuit is open.

**19. What's the difference between a liveness probe and a readiness probe?**
Liveness answers "is this process alive/healthy, or should it be restarted?" — failing it triggers a restart. Readiness answers "can this instance currently serve traffic?" — failing it removes the instance from the load balancer's rotation without restarting it (e.g. during startup, or while temporarily overloaded/warming a cache).

**20. Design a rate limiter for a public API that needs to allow short bursts but enforce an average rate.**
Token bucket: a bucket refills at a fixed rate (the average allowed rate) up to a max capacity (the burst allowance); each request consumes a token, and requests are rejected when the bucket is empty. This is exactly the shape needed — steady-state enforcement with burst tolerance — unlike a leaky bucket, which smooths everything to a constant rate with no burst allowance.

## Caching & Performance

**21. When would you choose write-through caching over cache-aside?**
When staleness is unacceptable and reads vastly outnumber writes for that data — write-through keeps the cache always fresh at the cost of extra write latency. Cache-aside is the better general-purpose default since it only caches what's actually requested and doesn't penalize every write.

**22. What is P95/P99 latency and why do teams care about it more than average latency?**
P95/P99 are the latency values below which 95%/99% of requests fall. Averages hide tail behavior — a service can have a great average latency while 1% of users experience multi-second delays. Since real users experience individual requests, not averages, P95/P99 better represent the actual worst-case experience a meaningful fraction of your users have.

## Observability & Testing

**23. What's the difference between a metric, a log, and a trace?**
A metric is an aggregated numeric measurement over time (request count, error rate). A log is a discrete, timestamped event with context. A trace follows a single request's journey across multiple services, showing where time was spent. They're complementary: metrics tell you *something* is wrong, logs and traces tell you *why*.

**24. Why is structured logging preferable to plain-text log lines in production?**
Structured logs (JSON, key-value) are machine-parseable, so you can filter, aggregate, and query them (e.g. "all errors for user_id=42 in the last hour") without regex-parsing free text. This is essential once you're at a scale where humans aren't reading logs line-by-line.

**25. What's the difference between unit, integration, and end-to-end tests, and how would you allocate test effort across them?**
Unit tests check a single function/class in isolation (fast, cheap, many). Integration tests check that components work together (e.g. API + real DB) (slower, fewer). End-to-end tests exercise the full deployed system as a user would (slowest, fewest, most valuable for catching real breakage). The typical guidance is a pyramid — most tests at the unit level, fewer at each level up — because higher-level tests are slower and more brittle.
