# Part 6 — Production Reliability

## What You'll Learn

How APIs stay correct and available when the network is unreliable, downstream services are slow or down, and traffic spikes unexpectedly: timeouts, retries, exponential backoff, jitter, idempotency, rate limiting, circuit breakers, bulkheads, graceful degradation, and health/readiness/liveness checks.

## Prerequisites

[Part 3 — Building APIs](../03-building-apis/README.md). Helpful: Part 4 (databases are a common source of the failures this part defends against).

## Chapters

| # | Chapter | Status |
|---|---|---|
| 1 | [Timeouts](timeouts.md) | ✅ Written |
| 2 | [Retries](retries.md) | ✅ Written |
| 3 | [Exponential Backoff](exponential-backoff.md) | ✅ Written |
| 4 | Jitter | 🚧 Planned |
| 5 | Idempotency in Practice | 🚧 Planned |
| 6 | [Rate Limiting](rate-limiting.md) | ✅ Written |
| 7 | [Circuit Breakers](circuit-breakers.md) | ✅ Written |
| 8 | Bulkheads | 🚧 Planned |
| 9 | Graceful Degradation | 🚧 Planned |
| 10 | Health Checks | 🚧 Planned |
| 11 | Readiness and Liveness Probes | 🚧 Planned |

> Note: chapter 5 here (`idempotency-in-practice.md`) covers *implementing* idempotency (idempotency keys, storage, replay behavior) as a reliability pattern — see [Part 2's idempotency chapter](../02-rest-api-design/idempotency.md) for the conceptual/HTTP-semantics introduction first.

## Related Example

[`examples/fastapi-crud/`](../../examples/fastapi-crud/) is extended with retry/backoff and rate-limiting middleware.

## Next

[Part 7 — Caching & Performance](../07-caching-performance/README.md)
