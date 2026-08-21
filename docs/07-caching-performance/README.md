# Part 7 — Caching & Performance

## What You'll Learn

Why caching exists, how to use Redis correctly, cache-aside and write-through patterns, TTLs, cache invalidation (the hard part), distributed caching, CDN basics, and how to reason about latency, throughput, and percentiles (P50/P95/P99).

## Prerequisites

[Part 4 — Databases & APIs](../04-databases-and-apis/README.md) (caching exists largely to protect databases).

## Chapters

| # | Chapter | Status |
|---|---|---|
| 1 | [Why Caching Matters](why-caching-matters.md) | ✅ Written |
| 2 | [Redis](redis.md) | ✅ Written |
| 3 | [Cache-Aside Pattern](cache-aside.md) | ✅ Written |
| 4 | Write-Through Caching | 🚧 Planned |
| 5 | TTL | 🚧 Planned |
| 6 | [Cache Invalidation](cache-invalidation.md) | ✅ Written |
| 7 | Distributed Caching | 🚧 Planned |
| 8 | CDN Basics | 🚧 Planned |
| 9 | Performance Bottlenecks | 🚧 Planned |
| 10 | [Latency and P95/P99](latency-and-percentiles.md) | ✅ Written |

## Related Example

[`examples/redis-cache/`](../../examples/redis-cache/) — cache-aside pattern implemented against a FastAPI endpoint.

## Next

[Part 8 — Async & Event-Driven Systems](../08-async-systems/README.md)
