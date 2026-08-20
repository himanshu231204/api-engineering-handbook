# Intermediate Exercises

Cross-chapter, mini-project-style tasks for readers comfortable with the basics of Parts 1–10 (through API Security) who are ready to combine reliability, caching, async, and real-time patterns.

## 1. Add Redis caching with cache-aside to a database-backed endpoint
**Relates to:** Part 4 (Databases & APIs), Part 7 (Cache-Aside, Redis)

Build (or extend) an API endpoint backed by a real Postgres database, then add a Redis cache-aside layer in front of a read-heavy endpoint. Measure and record the latency difference between a cache miss and a cache hit. Then implement invalidation: when the underlying row is updated via `PATCH`, delete the corresponding cache key, and prove it works by reading, updating, and reading again.

## 2. Implement retries with exponential backoff and jitter against a flaky dependency
**Relates to:** Part 6 (Retries, Exponential Backoff, Jitter)

Write a small HTTP client wrapper that calls an endpoint you control which randomly returns `500` about 40% of the time. Implement retry logic with exponential backoff and full jitter, capped at 5 attempts and a 10-second total time budget. Log every attempt's delay and outcome, and confirm your implementation never retries on a `400` response.

## 3. Build a circuit breaker around a failing dependency
**Relates to:** Part 6 (Circuit Breakers)

Implement a simple circuit breaker (closed/open/half-open) as a reusable wrapper (not tied to one specific call site) around calls to an external dependency. Write a test harness that makes the dependency fail consistently and confirms the breaker trips to `open` after your configured threshold, then verify it transitions to `half-open` after the cooldown and back to `closed` once the dependency "recovers" (flip your test dependency back to succeeding).

## 4. Implement idempotency keys for a non-idempotent POST endpoint
**Relates to:** Part 2 (Idempotency), Part 6 (Reliability)

Build a `POST /orders` endpoint that accepts an `Idempotency-Key` header. Store the key with the resulting response for a time window (e.g. 24 hours using Redis with a TTL). Send the same request twice with the same key and confirm the second call returns the identical response without creating a second order. Then confirm that reusing the key with a *different* request body is rejected (a real API shouldn't silently return the first result for a materially different request).

## 5. Move slow work to a background job queue
**Relates to:** Part 8 (Background Tasks, Job Queues, Workers, Message Queues)

Take an API endpoint that does something slow (simulate with a 5-second sleep, standing in for e.g. sending an email or generating a report). Refactor it so the endpoint enqueues a job and returns `202 Accepted` with a job ID immediately, a separate worker process consumes the queue and does the work, and a `GET /jobs/{id}` endpoint reports job status (`pending`/`running`/`done`/`failed`). Use Redis, RabbitMQ, or an in-process queue library — the point is the API/worker separation, not the specific broker.

## 6. Build a webhook sender with signature verification
**Relates to:** Part 9 (Webhooks, Webhook Signature Verification)

Build an endpoint that, when a resource changes, sends a signed webhook (HMAC-SHA256 over the raw payload with a shared secret) to a configured URL. Then build a small receiver endpoint that verifies the signature using constant-time comparison and rejects (`401`) requests with an invalid or missing signature. Add retry-with-backoff on the sender side for non-2xx responses.

## 7. Add Server-Sent Events for a live-updating feed
**Relates to:** Part 9 (Server-Sent Events)

Build an SSE endpoint that streams events (e.g. new notes being created) to connected clients in real time. Build a minimal HTML page (or script using an SSE client) that connects and logs each event as it arrives. Then simulate a client disconnecting mid-stream and confirm your server cleans up the connection instead of leaking it.

## 8. Implement CORS correctly for a public API
**Relates to:** Part 10 (CORS)

Configure CORS on your API so only a specific allowed origin (not `*`) can make cross-origin requests with credentials, and only for the methods/headers your API actually needs. Write a test (using `curl -X OPTIONS` or a browser) that confirms a disallowed origin is rejected and an allowed origin's preflight succeeds.

## 9. Harden an endpoint against SQL injection and validate the fix
**Relates to:** Part 10 (SQL Injection, Input Validation)

Take a deliberately vulnerable endpoint that builds a SQL query via string concatenation with user input, and demonstrate the vulnerability with a crafted input (in a local/sandboxed environment only). Then fix it using parameterized queries/an ORM, and re-run the same crafted input to confirm it's now treated as inert data.

## 10. Design and implement API versioning for a breaking change
**Relates to:** Part 2 (API Versioning)

Take an existing endpoint and make a genuinely breaking change to its response shape (e.g. renaming a field, changing a type). Implement it as a new `/v2/` version while keeping `/v1/` serving the old shape unchanged. Write a short migration note documenting the difference for API consumers, and add a `Deprecation` header to the `/v1/` responses.

## 11. Build a repository-pattern data layer and swap its backend
**Relates to:** Part 4 (Repository Pattern), Part 3 (Project Architecture)

Refactor your notes/orders API so all database access goes through a repository interface (not scattered raw queries in route handlers). Implement it once against Postgres, then implement a second in-memory fake repository conforming to the same interface, and use the fake in your test suite instead of a real database — demonstrate that your route/service tests pass against either implementation unchanged.

## 12. Measure and improve P95/P99 latency under load
**Relates to:** Part 7 (Latency and P95/P99), Part 13 (Load Testing)

Run a basic load test (e.g. with `locust`, `k6`, or `hey`) against one of your endpoints and record average, P95, and P99 latency. Identify the actual bottleneck (unindexed query, N+1 query, missing cache, synchronous slow work) and fix just one of them, then re-run the load test and compare the before/after P95/P99 numbers.

## 13. Write integration tests against a real containerized database
**Relates to:** Part 13 (Integration Testing, Test Databases)

Set up a test suite that spins up a real Postgres instance in a container (e.g. via `pytest` + `testcontainers` or Docker Compose), runs your migrations against it, and tests your repository/service layer against the real database rather than a mock. Confirm the test suite is repeatable — running it twice in a row should not fail due to leftover state from the first run.
