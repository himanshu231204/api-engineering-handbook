# AI Rate Limits

## Why This Matters

Every LLM provider caps how many requests you can send them in a given window — separate from, and in addition to, the token-based limits covered in [Token Rate Limits](token-rate-limits.md). Hit that cap and the provider stops accepting new requests with an HTTP 429, often for the rest of the current minute. If your gateway just forwards that failure straight to whichever internal service happened to be calling it, you get cascading errors across every feature that shares that provider — even features that individually sent very few requests. This chapter is about the general concept of provider-imposed **rate limits** (as opposed to token-volume limits) and how to build a gateway that absorbs 429s instead of propagating them.

This is the same reliability discipline covered generally in [Part 6 — Production Reliability](../06-production-reliability/README.md) and specifically [Rate Limiting](../06-production-reliability/rate-limiting.md) — applied here to the specific, asymmetric relationship you have with an LLM provider: they set the limit, you don't control it, and it can change without much notice.

## Core Concept

Provider rate limits typically come in a few flavors, often combined:

- **Requests per minute (RPM)** — a hard cap on the count of API calls, regardless of size.
- **Concurrent request limits** — a cap on how many in-flight requests you can have open at once, independent of your per-minute rate.
- **Tier-based limits** — most providers scale your limits with account tier/spend history, so a limit that's fine in staging can be tight in production, and a limit that's fine today can be tight after a traffic-driving launch.

When you exceed any of these, the provider responds with `429 Too Many Requests`, usually including a `Retry-After` header (or an equivalent field) telling you how long to wait before trying again. The core engineering problem is: **your gateway serves many internal callers concurrently, but the provider only sees one client (you) with one shared limit.** Without coordination, ten internal services can each independently believe they have "room" to call the provider, collectively blow through the shared limit, and all get 429s at once.

## Mental Model

Think of the provider's rate limit as a **single-lane toll booth** shared by every car (request) from every department in your company, even though each department thinks it has its own road. If five departments each send cars without coordinating, the booth backs up and rejects cars regardless of which department they came from. The fix isn't to make each department drive faster — it's to have one shared dispatcher (the gateway) that knows the toll booth's actual throughput and metering entry onto the road accordingly, so departments experience smooth, predictable service instead of a pileup they can't see the cause of.

## How It Works

1. The gateway tracks, per provider, the current rate of requests sent — typically via a **token bucket** or **sliding window counter** sized to match the provider's documented (or empirically observed) RPM and concurrency limits, kept comfortably under the true ceiling as a safety margin.
2. Before sending a request to a provider, the gateway checks whether capacity is available. If not, the request is either **queued** (held briefly, retried once capacity frees up) or **rejected immediately** with a 429 back to the internal caller — the right choice depends on the caller's own latency tolerance.
3. When the provider itself returns a 429, the gateway must **not** treat this as a generic failure — it should respect `Retry-After` if present, back off, and typically prefer failing over to a different provider (see [Fallback Systems](fallback-systems.md)) rather than queuing behind a limit that's already been hit.
4. The gateway applies **backpressure** upstream: if its own queue for a provider grows past a threshold, it should reject new requests fast (fail fast) rather than let queue depth grow unbounded and turn a rate-limit problem into a memory and latency problem.
5. Per-tenant or per-feature sub-limits (see [Cost Tracking](cost-tracking.md)) can be layered on top of the provider-wide limit, so one noisy internal caller can't consume the entire shared budget and starve every other feature.

## Architecture

```mermaid
sequenceDiagram
    participant S1 as Service A
    participant S2 as Service B
    participant GW as Gateway Rate Limiter
    participant P as Provider

    S1->>GW: generate() request
    S2->>GW: generate() request
    GW->>GW: check shared token bucket for Provider
    GW->>P: request from S1 (capacity available)
    GW-->>S2: 429 (queue full / capacity exhausted)
    P-->>GW: 200 OK
    GW-->>S1: response

    Note over GW,P: Bucket refills over time; S2 retries later
    S2->>GW: generate() request (retry)
    GW->>P: request from S2 (capacity now available)
    P-->>GW: 200 OK
    GW-->>S2: response
```

## Request / Response Example

The provider's raw 429 response the gateway must interpret correctly:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 8
Content-Type: application/json

{
  "error": {
    "type": "rate_limit_error",
    "message": "Number of request tokens has exceeded your per-minute rate limit."
  }
}
```

What the gateway returns to an internal caller when it has to reject a request due to its own local rate-limit protection (before ever reaching the provider) — note the internal 429 carries the same `Retry-After` semantics so callers can implement consistent backoff regardless of which layer rejected them:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3
Content-Type: application/json

{
  "error": "provider_rate_limited",
  "message": "Provider request capacity temporarily exhausted, retry shortly.",
  "provider": "provider_a"
}
```

## Code Example

A token-bucket limiter guarding *request count* (as opposed to token volume, covered in the next chapter), shared across all callers of a given provider:

```python
import asyncio
import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    """Classic token bucket: capacity tokens, refilled at `refill_rate` per
    second. Used here to limit REQUEST COUNT, not token volume — see
    token-rate-limits.md for the token-volume variant."""
    capacity: float
    refill_rate: float  # tokens (i.e. requests) per second
    _tokens: float = 0.0
    _last_refill: float = 0.0

    def __post_init__(self):
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def try_acquire(self, amount: float = 1.0) -> bool:
        self._refill()
        if self._tokens >= amount:
            self._tokens -= amount
            return True
        return False

    def seconds_until_available(self, amount: float = 1.0) -> float:
        self._refill()
        if self._tokens >= amount:
            return 0.0
        return (amount - self._tokens) / self.refill_rate


class ProviderRequestLimiter:
    """One bucket per provider, sized just under the provider's documented
    RPM limit to leave headroom for other clients/regions the provider
    itself might be balancing against."""

    def __init__(self, limits: dict[str, tuple[int, float]]):
        # limits: {provider_name: (capacity, refill_rate_per_second)}
        self._buckets = {
            name: TokenBucket(capacity=cap, refill_rate=rate)
            for name, (cap, rate) in limits.items()
        }

    async def acquire(self, provider: str, max_wait_seconds: float = 2.0) -> bool:
        """Attempts to acquire capacity, waiting briefly (bounded) rather than
        failing immediately on transient contention. Returns False if
        capacity doesn't free up within max_wait_seconds — caller should
        then reject or fall back rather than wait indefinitely."""
        bucket = self._buckets[provider]
        if bucket.try_acquire():
            return True

        wait = bucket.seconds_until_available()
        if wait > max_wait_seconds:
            return False  # fail fast — don't queue indefinitely

        await asyncio.sleep(wait)
        return bucket.try_acquire()


# Example: provider documents 500 requests/minute -> ~8.3/sec; we configure
# ourselves to 90% of that as a safety margin against clock drift and
# other clients sharing the same account.
limiter = ProviderRequestLimiter({
    "provider_a": (50, 7.5),   # burst capacity 50, steady ~7.5 req/sec
    "provider_b": (30, 4.0),
})
```

## Production Considerations

- **Provider-published limits are often the ceiling, not a guarantee.** Actual throughput can be lower under provider-side load. Treat published limits as an upper bound and tune your internal bucket down further based on observed 429 rates.
- **Concurrency limits need their own guard**, separate from RPM — a semaphore per provider, sized to the documented concurrent-request cap, prevents burst traffic from opening more simultaneous connections than the provider allows even if RPM has headroom.
- **Rate limit state must be shared across gateway replicas** in any horizontally scaled deployment (e.g., a Redis-backed token bucket), or each replica will independently believe it has the full quota, multiplying your effective request rate past what the provider actually allows.
- **429 handling belongs in the adapter's error normalization** (see [Multi-Provider Architecture](multi-provider-architecture.md)) so routing and fallback logic can react to `ProviderRateLimited` uniformly, regardless of provider-specific header names.

## Common Mistakes

- **Conflating request-rate limits with token-rate limits** and building only one limiter — a request that's small in count but huge in tokens can still get rate-limited on the token dimension even when comfortably under the RPM cap (see [Token Rate Limits](token-rate-limits.md)).
- **Retrying into a 429 immediately** without respecting `Retry-After`, which usually just extends the penalty window with the provider.
- **No shared state across replicas**, so local-only rate limiters silently exceed the true provider limit as the gateway scales horizontally.
- **Unbounded queuing** on rate-limit contention, which turns a rate-limit problem into a memory-growth and tail-latency problem during sustained high traffic.

## Best Practices

- Size your internal limiter comfortably below the provider's documented limit (e.g., 80-90%), and monitor actual 429 rates to tune it over time.
- Track concurrency and request-rate as two separate guards, not one.
- Prefer failing fast with a clear, typed error over unbounded queuing when capacity is exhausted — let calling services decide whether to retry, fall back to a lower-priority path, or surface a "try again" message to the end user.
- Alert on sustained 429 rates against a provider — this is often an early signal that traffic has grown past what your current provider tier supports, well before it becomes a full incident.

## AI Engineering Perspective

Agent loops (see [Part 17 — AI Agents & MCP](../17-ai-agents-and-mcp/README.md)) are one of the fastest ways to accidentally blow through a provider's request-rate limit, because a single user interaction can fan out into many sequential or parallel tool-augmented LLM calls — a request-rate limiter sized for "one call per user action" will be badly wrong for agentic traffic, which needs per-agent-run budgets in addition to global provider limits. In RAG pipelines (see [Part 16 — RAG APIs](../16-rag-apis/README.md)), embedding calls during bulk document ingestion (see [Part 16](../16-rag-apis/README.md)) are a classic source of request-rate exhaustion, since ingestion jobs naturally want to fire many embedding requests in a tight loop — batching multiple chunks into a single embedding request, where the provider's API supports it, is usually a much better fix than simply widening the rate limiter.

## Exercises

**Beginner:** Given a provider documented at 300 requests/minute, calculate a reasonable token-bucket `capacity` and `refill_rate` with a 15% safety margin.

**Intermediate:** Extend `ProviderRequestLimiter` to also enforce a concurrency cap (max in-flight requests) using an `asyncio.Semaphore` per provider, alongside the existing rate limiter.

**Advanced:** Design how you'd share `TokenBucket` state across multiple gateway replicas using Redis (see [Redis](../07-caching-performance/redis.md)), including how to keep the refill calculation correct despite clock drift and network latency between replicas.

## Key Takeaways

- Providers enforce request-count and concurrency limits independent of token volume; exceeding either produces a 429.
- A shared, provider-wide limiter (not per-caller) is required because internal callers don't coordinate with each other by default.
- Fail fast on exhausted capacity rather than queuing unboundedly; let callers decide how to react.
- Rate-limit state must be shared across gateway replicas in any horizontally scaled deployment, or your effective limit silently multiplies with replica count.
