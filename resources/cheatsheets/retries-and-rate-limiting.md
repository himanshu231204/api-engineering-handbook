# Retries & Rate Limiting Cheatsheet

For the full explanation, see [Production API Reliability](../../docs/06-production-reliability/README.md).

## Exponential backoff formula

```
delay = min(base_delay * (2 ^ attempt), max_delay)
```

- `base_delay` — starting delay (e.g. 100ms).
- `attempt` — 0-indexed retry attempt number.
- `max_delay` — cap so delays don't grow unbounded (e.g. 30s).

**With jitter** (recommended — prevents synchronized "retry storms" from many clients backing off in lockstep):

```
# Full jitter
delay = random(0, min(max_delay, base_delay * 2^attempt))

# Equal jitter
delay = (min(max_delay, base_delay * 2^attempt) / 2) + random(0, same / 2)
```

- Use **full jitter** for most cases — it spreads retries out the most.
- Always cap total retry attempts (e.g. 3–5) and/or a total elapsed-time budget.
- Only retry on transient/idempotent-safe failures: timeouts, `429`, `503`, connection resets. Never blindly retry `400`/`404`/`422` (they won't succeed) or non-idempotent `POST` without an idempotency key.

## Rate-limiting algorithm comparison

| Algorithm | How it works | Bursts allowed? | Memory | Precision | Best for |
|---|---|---|---|---|---|
| **Fixed window** | Count requests per fixed time window (e.g. 00:00–00:59); reset counter at window boundary | Yes, at window edges (2x burst possible right at boundary) | Very low (1 counter per key) | Low | Simple, cheap rate limiting where boundary bursts are acceptable |
| **Sliding window log** | Store timestamp of every request; count requests within the last N seconds from *now* | No | High (stores every request timestamp) | Exact | Low-volume, high-precision limits |
| **Sliding window counter** | Weighted average of current and previous fixed windows | Minimal | Low | Approximate but good | Good balance of accuracy and cost — common production default |
| **Token bucket** | Bucket holds tokens, refilled at a fixed rate; each request consumes a token; requests rejected when bucket is empty | Yes, up to bucket capacity | Low (2 numbers per key) | High | APIs wanting to allow controlled bursts (most common choice, e.g. AWS, Stripe) |
| **Leaky bucket** | Requests queue into a bucket that drains (processes) at a fixed rate; overflow is rejected | No — smooths bursts into a constant output rate | Low | High | Smoothing traffic to a constant downstream rate (e.g. protecting a fixed-capacity worker) |

**Token bucket vs leaky bucket**, in one line: token bucket controls *how much* can go through (allows bursts up to capacity); leaky bucket controls *how fast* it goes through (enforces a constant output rate).

## Circuit breaker states (quick reference)

| State | Behavior | Transitions to |
|---|---|---|
| **Closed** | Requests flow normally; failures are tracked | → **Open** when failure rate crosses threshold |
| **Open** | Requests fail immediately without calling the dependency | → **Half-open** after cooldown timer expires |
| **Half-open** | A limited number of trial requests are allowed through | → **Closed** if trials succeed; → **Open** if trials fail |

## Retry checklist

- [ ] Is the operation idempotent, or protected by an idempotency key?
- [ ] Am I retrying only on transient errors (timeouts, `429`, `502`/`503`/`504`, connection errors)?
- [ ] Do I have exponential backoff with jitter, not fixed-interval retries?
- [ ] Is there a max retry count AND a max total time budget?
- [ ] Am I respecting a `Retry-After` header if the server sent one?
- [ ] Is there a circuit breaker around this dependency so retries stop during a sustained outage?
