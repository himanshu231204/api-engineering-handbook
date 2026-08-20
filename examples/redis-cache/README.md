# Redis Cache-Aside Pattern

Accompanies [Part 7 — Caching & Performance](../../docs/07-caching-performance/README.md),
especially [Redis](../../docs/07-caching-performance/redis.md),
[Cache-Aside](../../docs/07-caching-performance/cache-aside.md), and
[Cache Invalidation](../../docs/07-caching-performance/cache-invalidation.md) (TTL is covered within
[Why Caching Matters](../../docs/07-caching-performance/why-caching-matters.md); a standalone TTL chapter is planned).

## What this demonstrates

The cache-aside pattern, made visible: `GET /products/{id}` checks Redis first, and only
falls through to a simulated slow "database" call (`asyncio.sleep(1.5)`) on a cache miss.
The response carries an `X-Cache: HIT` or `X-Cache: MISS` header so you can watch the
effect directly instead of trusting it happened.

```text
request -> check Redis
             |-- HIT  -> return cached value (fast, X-Cache: HIT)
             `-- MISS -> slow "DB" call
                          -> write result into Redis with a TTL
                          -> return value (slow, X-Cache: MISS)
```

`DELETE /cache/products/{id}` demonstrates explicit invalidation — evicting an entry
before its TTL expires, which you'd do after updating the underlying data.

## Prerequisites

- Python 3.11+
- Docker (to run Redis via the included `docker-compose.yml`) — or any Redis instance
  you already have running.

## How to run it

```bash
cd examples/redis-cache
docker compose up -d          # starts Redis on localhost:6379

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload
```

By default the app connects to `redis://localhost:6379/0` — set `REDIS_URL` to point it
elsewhere.

## Try it

```bash
# First request: cache miss, ~1.5s, X-Cache: MISS
time curl -i http://127.0.0.1:8000/products/1

# Second request: cache hit, near-instant, X-Cache: HIT
time curl -i http://127.0.0.1:8000/products/1

# Unknown id: 404, still tagged X-Cache: MISS (nothing was cached)
curl -i http://127.0.0.1:8000/products/999

# Invalidate, then confirm the next request is a MISS again
curl -i -X DELETE http://127.0.0.1:8000/cache/products/1
curl -i http://127.0.0.1:8000/products/1
```

You can also inspect the cache directly:

```bash
docker compose exec redis redis-cli GET product:1
docker compose exec redis redis-cli TTL product:1
```

## Things to try

1. **Watch the TTL expire.** Set `CACHE_TTL_SECONDS=10`, fetch a product (MISS, then
   HIT), then wait 10+ seconds and fetch it again — you should see `X-Cache: MISS` once
   more without calling the delete endpoint. This is the "self-healing" half of caching:
   stale data disappears on its own even if nothing explicitly invalidates it.
2. **Introduce a cache stampede.** Remove the TTL (set `CACHE_TTL_SECONDS` very high) and
   imagine 1,000 concurrent requests arriving for a product that's *never* been cached —
   every one of them will independently take the slow path and hit the "database" at
   once. This is why production cache-aside implementations often add a lock or
   request-coalescing step around the miss path.
3. **Switch to write-through.** Add a `PUT /products/{id}` endpoint that updates
   `_FAKE_DB` *and* writes straight into Redis in the same request, instead of just
   deleting the cache key — compare this write-through approach to the invalidate-on-write
   approach already here, and think about which one risks serving stale data under a
   race condition.
