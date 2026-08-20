"""
Minimal multi-provider LLM gateway, exposed via a FastAPI `/chat` endpoint.

Ties together provider adapters (providers.py), routing-with-fallback and a
token-bucket rate limiter (gateway.py), and per-request cost tracking.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from gateway import (
    AllProvidersFailedError,
    TokenBucketRateLimiter,
    compute_cost_usd,
    route,
)
from providers import ProviderAAdapter, ProviderBAdapter, UnreliableTestAdapter

app = FastAPI(title="Minimal Multi-Provider LLM Gateway Example")

# Priority order: try the flaky test adapter first (it fails ~50% of the
# time by default with zero configuration), then fall back to provider_a,
# then provider_b. This makes the fallback path visible out of the box —
# re-run POST /chat a few times and watch the "provider" field in the
# response switch between "flaky_test_provider" and "provider_a" as
# requests succeed or fall through. See the README.
PROVIDER_PRIORITY = [UnreliableTestAdapter(), ProviderAAdapter(), ProviderBAdapter()]

# One shared limiter for the whole gateway process in this demo. A real
# deployment scopes limiters per tenant (and backs them with shared storage
# like Redis) — see ../../docs/15-production-ai-systems/ai-rate-limits.md
# and ../../docs/15-production-ai-systems/token-rate-limits.md.
rate_limiter = TokenBucketRateLimiter(capacity=5, refill_rate=1.0)

# In-memory usage ledger: one entry per request. A real gateway writes this
# to a durable, queryable store instead. See
# ../../docs/15-production-ai-systems/cost-tracking.md.
usage_ledger: list[dict] = []


class ChatRequest(BaseModel):
    tenant_id: str = Field(..., description="Who is calling, for cost attribution.")
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=300, ge=1, le=4000)


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not await rate_limiter.allow():
        raise HTTPException(status_code=429, detail="rate limit exceeded, try again shortly")

    try:
        result = await route(
            request.prompt,
            providers=PROVIDER_PRIORITY,
            max_tokens=request.max_tokens,
            timeout_seconds=5.0,
        )
    except AllProvidersFailedError as exc:
        raise HTTPException(status_code=503, detail={"message": "all providers unavailable", "errors": exc.errors})

    cost_usd = compute_cost_usd(result)

    usage_ledger.append(
        {
            "tenant_id": request.tenant_id,
            "provider": result.provider,
            "model": result.model,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost_usd": cost_usd,
        }
    )

    return ChatResponse(
        content=result.content,
        provider=result.provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=cost_usd,
        latency_ms=result.latency_ms,
    )


@app.get("/usage")
async def usage_summary() -> dict:
    """Very small illustrative rollup of the in-memory usage ledger, by
    tenant. Real cost dashboards aggregate a durable ledger by tenant,
    feature, model, and time window — see
    ../../docs/15-production-ai-systems/cost-tracking.md."""
    by_tenant: dict[str, dict] = {}
    for entry in usage_ledger:
        bucket = by_tenant.setdefault(entry["tenant_id"], {"requests": 0, "total_cost_usd": 0.0})
        bucket["requests"] += 1
        bucket["total_cost_usd"] = round(bucket["total_cost_usd"] + entry["cost_usd"], 6)
    return by_tenant
