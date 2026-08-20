# Caching Cheatsheet

For the full explanation, see [Caching & Performance](../../docs/07-caching-performance/README.md).

## Caching strategy comparison

| Strategy | Write path | Read path | Pros | Cons | Best for |
|---|---|---|---|---|---|
| **Cache-aside (lazy loading)** | App writes to DB only; cache is not updated | App checks cache first; on miss, reads DB and populates cache | Simple, only caches what's actually requested, cache failures don't break writes | First request after a miss/expiry is slow (cold cache); risk of stale data until TTL expires | Most general-purpose read-heavy workloads |
| **Write-through** | App writes to cache and DB synchronously (cache is updated as part of the write) | App reads from cache, which is always fresh | Cache is never stale, reads are always fast | Extra latency on every write; wasted cache space for rarely-read data | Data that's read far more often than it's written, where staleness is unacceptable |
| **Write-behind (write-back)** | App writes to cache; cache asynchronously flushes to DB later | App reads from cache | Very fast writes, can batch/coalesce DB writes | Risk of data loss if cache crashes before flush; added complexity | Write-heavy workloads that can tolerate eventual durability (e.g. metrics, counters) |
| **Read-through** | App writes to DB directly | Cache itself is responsible for loading from DB on a miss (transparent to the app) | Simplifies application code (no manual cache-population logic) | Requires cache library/provider support | Systems where the caching layer supports it natively (e.g. some ORMs, CDNs) |

## TTL guidance

- **Short TTL (seconds–minutes)** — rapidly changing data (stock prices, live counters), or data where staleness is costly.
- **Medium TTL (minutes–hours)** — typical API responses, user profile data, product catalogs.
- **Long TTL (hours–days)** — rarely-changing reference data (country lists, config, static content).
- **No expiry + explicit invalidation** — data where you can reliably invalidate on every write (requires discipline, higher risk if you miss a path).
- Rule of thumb: set TTL based on how *stale* the data is allowed to be, not how often it changes — then use invalidation to handle the cases where staleness genuinely can't wait.

## Cache invalidation strategies (quick reference)

| Strategy | How | Tradeoff |
|---|---|---|
| **TTL expiry** | Let entries expire naturally after a fixed time | Simple, but data can be stale for up to the full TTL |
| **Explicit invalidation on write** | App deletes/updates the cache key when the underlying data changes | Fresh data, but easy to miss a code path and leave stale entries |
| **Versioned keys** | Include a version number in the cache key (`user:42:v3`); bump version on write | Avoids race conditions of delete-then-repopulate; old versions just expire naturally |
| **Event-driven invalidation** | A write publishes an event (e.g. via a message queue) that consumers use to invalidate their caches | Scales across many services/caches, but adds infrastructure and latency before invalidation lands |

## The two hardest problems in caching

1. **Stale reads** — solved by choosing the right combination of TTL + invalidation strategy above.
2. **Cache stampede** ("thundering herd") — many requests miss the cache simultaneously (e.g. right after expiry) and all hit the DB at once. Mitigate with:
   - **Locking/single-flight** — only one request repopulates the cache, others wait for it.
   - **Early refresh** — refresh the cache slightly before it expires (probabilistic early expiration).
   - **Stale-while-revalidate** — serve stale data while one request refreshes it in the background.

## Common mistakes

- Caching without a TTL "just in case" — stale-forever data with no invalidation path.
- Caching error responses or `null` results without a much shorter TTL, causing "negative caching" outages.
- Cache key collisions from not including all relevant parameters (user ID, locale, filters) in the key.
- Forgetting cache invalidation entirely when using write-through only in some code paths, not all.
