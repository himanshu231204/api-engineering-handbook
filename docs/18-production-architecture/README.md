# Part 18 — Production Architecture

## What You'll Learn

This part zooms all the way out and walks through one complete, production-grade system end to end — the composite of everything Parts 1–17 covered individually: client → CDN/load balancer → API gateway (auth, rate limiting) → application services → database/cache/queue → AI gateway → LLM providers → observability stack.

```text
Client
   │
   ▼
CDN / Load Balancer
   │
   ▼
API Gateway
   │
   ├── Authentication
   ├── Rate Limiting
   │
   ▼
Application Services
   │
 ┌─┼─────────────┐
 ▼ ▼             ▼
DB Cache       Queue
 │  │             │
 ▼  ▼             ▼
Postgres Redis Workers
                  │
                  ▼
             AI Gateway
                  │
            ┌─────┼─────┐
            ▼     ▼     ▼
           LLM   LLM   LLM
```

## Prerequisites

Parts 1–17. This part assumes you've read (or at least skimmed) every layer it references.

## Chapters

| # | Chapter | Status |
|---|---|---|
| 1 | [Complete Architecture Walkthrough](complete-architecture-walkthrough.md) | ✅ Written |
| 2 | [Request Flow, End to End](request-flow.md) | ✅ Written |
| 3 | [Failure Scenarios](failure-scenarios.md) | ✅ Written |
| 4 | [Scaling Strategy](scaling-strategy.md) | ✅ Written |
| 5 | [Security in Production](security-in-production.md) | ✅ Written |
| 6 | [Observability in Production](observability-in-production.md) | ✅ Written |
| 7 | [Cost Management](cost-management.md) | ✅ Written |

## Related Diagram

[`diagrams/production-ai-architecture.md`](../../diagrams/production-ai-architecture.md).

## Next

[Part 19 — System Design Case Studies](../19-system-design-case-studies/README.md)
