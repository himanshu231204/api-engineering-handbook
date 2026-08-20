"""
Cache-aside pattern against a simulated slow "database", using Redis.

Flow on every GET /products/{id}:
    1. Check Redis for the key.
    2. HIT  -> return the cached value immediately.
    3. MISS -> run the slow lookup, write the result into Redis with a TTL,
               then return it.

The `X-Cache: HIT` / `X-Cache: MISS` response header makes the effect
visible from curl -- hit the same endpoint twice and watch the header (and
the latency) change. See docs/07-caching-performance/cache-aside.md and
docs/07-caching-performance/ttl.md.

Run it (Redis must be running -- see docker-compose.yml):
    docker compose up -d
    uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "30"))
SIMULATED_DB_LATENCY_SECONDS = float(os.environ.get("SIMULATED_DB_LATENCY_SECONDS", "1.5"))

# A tiny fake "database" so this example needs nothing but Redis running.
_FAKE_DB: dict[int, dict] = {
    1: {"id": 1, "name": "Mechanical Keyboard", "price_usd": 129.0},
    2: {"id": 2, "name": "4K Monitor", "price_usd": 349.0},
    3: {"id": 3, "name": "USB-C Dock", "price_usd": 79.0},
}


class Product(BaseModel):
    id: int
    name: str
    price_usd: float


redis_client: redis.Redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    yield
    await redis_client.aclose()


app = FastAPI(title="Cache-Aside Example", version="1.0.0", lifespan=lifespan)


async def fetch_product_from_db(product_id: int) -> dict | None:
    """Stands in for a slow database/upstream-service call."""
    await asyncio.sleep(SIMULATED_DB_LATENCY_SECONDS)
    return _FAKE_DB.get(product_id)


def _cache_key(product_id: int) -> str:
    return f"product:{product_id}"


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int, response: Response) -> Product:
    key = _cache_key(product_id)

    cached = await redis_client.get(key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return Product.model_validate(json.loads(cached))

    product = await fetch_product_from_db(product_id)
    if product is None:
        # Headers on the injected `response` object are ignored once an
        # exception is raised -- pass them to HTTPException directly instead.
        raise HTTPException(
            status_code=404,
            detail=f"No product with id {product_id}",
            headers={"X-Cache": "MISS"},
        )

    # Cache-aside: populate the cache only *after* a successful fetch, with
    # a TTL so stale data self-expires even if nothing explicitly
    # invalidates it. See docs/07-caching-performance/cache-invalidation.md.
    await redis_client.set(key, json.dumps(product), ex=CACHE_TTL_SECONDS)

    response.headers["X-Cache"] = "MISS"
    return Product.model_validate(product)


@app.delete("/cache/products/{product_id}", status_code=204)
async def invalidate_product_cache(product_id: int) -> Response:
    """Manually evict a product from the cache -- e.g. after an update, so
    stale data isn't served until the TTL naturally expires."""
    await redis_client.delete(_cache_key(product_id))
    return Response(status_code=204)


@app.get("/health")
async def health() -> dict:
    pong = await redis_client.ping()
    return {"status": "ok", "redis_connected": pong}
