# Part 8 — Async & Event-Driven Systems

## What You'll Learn

How to move work outside the request/response cycle: sync vs. async APIs, Python's `asyncio`, background tasks, job queues, workers, message queues, RabbitMQ and Kafka concepts, event-driven architecture, and eventual consistency (plus delivery guarantees: at-least-once, at-most-once, and why "exactly-once" is mostly a marketing term).

## Prerequisites

[Part 6 — Production Reliability](../06-production-reliability/README.md).

## Chapters

| # | Chapter | Status |
|---|---|---|
| 1 | [Sync vs Async](sync-vs-async.md) | ✅ Written |
| 2 | [Python asyncio](python-asyncio.md) | ✅ Written |
| 3 | [Background Tasks](background-tasks.md) | ✅ Written |
| 4 | Job Queues | 🚧 Planned |
| 5 | Workers | 🚧 Planned |
| 6 | [Message Queues](message-queues.md) | ✅ Written |
| 7 | RabbitMQ Concepts | 🚧 Planned |
| 8 | Kafka Concepts | 🚧 Planned |
| 9 | Event-Driven Architecture | 🚧 Planned |
| 10 | Eventual Consistency | 🚧 Planned |

## Related Example

[`examples/background-jobs/`](../../examples/background-jobs/) — a queue + worker pattern for offloading slow work from a request.

## Related Project

[Project 5 — Async Document Processing Pipeline](../../projects/05-document-processing/) applies everything in this part directly.

## Next

[Part 9 — Real-Time APIs & Webhooks](../09-realtime-and-webhooks/README.md)
