# Minimal Multi-Provider LLM Gateway

A small but complete illustration of the LLM gateway pattern: an abstract
`ProviderAdapter` interface, multiple concrete provider adapters, priority-
ordered routing with fallback, a token-bucket rate limiter, and basic
per-request cost tracking — all wired into one FastAPI `/chat` endpoint.

Accompanies: [`docs/15-production-ai-systems/llm-gateways.md`](../../docs/15-production-ai-systems/llm-gateways.md)
(and specifically
[`multi-provider-architecture.md`](../../docs/15-production-ai-systems/multi-provider-architecture.md),
[`model-routing.md`](../../docs/15-production-ai-systems/model-routing.md),
[`fallback-systems.md`](../../docs/15-production-ai-systems/fallback-systems.md), and
[`cost-tracking.md`](../../docs/15-production-ai-systems/cost-tracking.md))

## What This Demonstrates

- **`providers.py`**:
  - `ProviderAdapter` — an abstract base class every provider implements
    (`generate(prompt, max_tokens, timeout_seconds) -> GenerationResult`),
    so gateway logic never has to know which concrete provider it's
    calling.
  - `ProviderAAdapter` / `ProviderBAdapter` — illustrative adapters for an
    Anthropic-style and an OpenAI-compatible-style API respectively, each
    reading its own API key from a different environment variable. Without
    a key set, each simulates a response locally; with a key set, each
    routes to a `_call_real_api` stub with a clearly-commented
    pseudo-implementation showing the real HTTP call's shape.
  - `UnreliableTestAdapter` — a third, credential-free adapter that fails a
    configurable fraction of the time (`FLAKY_PROVIDER_FAILURE_RATE`,
    default 50%), so the fallback path is easy to see without needing to
    actually take down a real provider.
- **`gateway.py`**:
  - `route()` — tries providers in priority order, catching
    `ProviderUnavailableError` and falling through to the next one;
    raises `AllProvidersFailedError` (with every provider's error attached)
    if all fail.
  - `TokenBucketRateLimiter` — a simple in-memory token-bucket limiter
    (capacity + refill rate).
  - `PRICING_TABLE` + `compute_cost_usd()` — an illustrative per-provider,
    per-model USD-per-1k-token pricing table used to attach a `cost_usd` to
    every response.
- **`main.py`** — `POST /chat` ties it all together: rate-limit check ->
  routed generation call with fallback -> cost computation -> append to an
  in-memory usage ledger. `GET /usage` gives a tiny per-tenant cost rollup
  from that ledger.

## Prerequisites

- Python 3.11+
- No provider accounts required to run the demo (see above).

## How to Run

```bash
cd examples/llm-gateway
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: only needed for real providers / tuning the demo
uvicorn main:app --reload
```

Call the gateway a handful of times and watch which provider serves each
request:

```bash
for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"tenant_id": "acme_corp", "prompt": "Summarize the Q3 roadmap."}' \
  | python3 -c "import sys, json; d = json.load(sys.stdin); print(d['provider'], d['cost_usd'])"
done
```

With the default 50% simulated failure rate on `flaky_test_provider`, you
should see the served provider alternate between `flaky_test_provider` and
`provider_a` across calls — that's the fallback path (`gateway.route()`)
working.

Check the per-tenant cost rollup:

```bash
curl -s http://localhost:8000/usage
```

Trigger the rate limiter (bucket capacity is 5, refills at 1/sec by
default — fire requests faster than that):

```bash
for i in $(seq 1 8); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"tenant_id": "acme_corp", "prompt": "hi"}'
done
# expect some 429s once the bucket empties
```

## Using Real Providers

1. Set `PROVIDER_A_API_KEY` and/or `PROVIDER_B_API_KEY` in `.env`.
2. In `providers.py`, implement the corresponding adapter's `_call_real_api`
   method, following the shape shown in its docstring — a generic HTTP
   POST to the provider's chat completion endpoint. Make sure your
   implementation raises `ProviderUnavailableError` (not lets the raw
   exception propagate) on timeout or a non-2xx response, so
   `gateway.route()` can correctly fall back to the next provider.
3. Add real per-model pricing to `PRICING_TABLE` in `gateway.py` — the
   table only has entries for the two illustrative demo models by default.
4. Restart the server.

## Things to Try / Modify

1. **Make fallback exhaustive** — set `PROVIDER_A_API_KEY` and
   `PROVIDER_B_API_KEY` to some placeholder value without implementing
   `_call_real_api` (it will raise `NotImplementedError`, which
   `gateway.route()` does *not* currently catch) and observe the
   unhandled error — then decide whether `route()` should also treat
   unexpected exceptions as "try the next provider," and if so, where the
   line should be drawn between "this provider is unavailable" and "this
   is a bug that should surface loudly."
2. **Scope the rate limiter per tenant** — right now `rate_limiter` is one
   shared bucket for every caller. Change it to a `dict[str,
   TokenBucketRateLimiter]` keyed by `tenant_id` so tenants can't exhaust
   each other's budget. See
   [`docs/15-production-ai-systems/ai-rate-limits.md`](../../docs/15-production-ai-systems/ai-rate-limits.md).
3. **Add a circuit breaker** — instead of always trying
   `flaky_test_provider` first, track its recent failure rate and skip it
   for a cooldown period once it crosses a threshold, per
   [`docs/06-production-reliability/circuit-breakers.md`](../../docs/06-production-reliability/circuit-breakers.md).
4. **Persist the usage ledger** — swap the in-memory `usage_ledger` list
   for real storage (a database table or an append-only log) so cost data
   survives a restart, per
   [`docs/15-production-ai-systems/cost-tracking.md`](../../docs/15-production-ai-systems/cost-tracking.md).
