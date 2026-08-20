# Project 8 — Multi-Provider LLM Gateway

## Goal

Build a gateway API that sits between your applications and multiple LLM providers (e.g. OpenAI, Anthropic, and a local/open-source model), presenting one consistent API while handling routing, automatic fallback, per-key rate limiting, and cost tracking underneath. This is the project that teaches you why nobody calls provider APIs directly in production: providers go down, prices differ, rate limits are per-provider, and you need one place to answer "how much did tenant X spend on LLM calls this month?"

## Builds On

- [Part 15 — Production AI Systems](../../docs/15-production-ai-systems/README.md)
- Specifically: [LLM gateways](../../docs/15-production-ai-systems/llm-gateways.md), [multi-provider architecture](../../docs/15-production-ai-systems/multi-provider-architecture.md), [model routing](../../docs/15-production-ai-systems/model-routing.md), [fallback systems](../../docs/15-production-ai-systems/fallback-systems.md), [AI rate limits](../../docs/15-production-ai-systems/ai-rate-limits.md), [token rate limits](../../docs/15-production-ai-systems/token-rate-limits.md), [cost tracking](../../docs/15-production-ai-systems/cost-tracking.md), [prompt caching](../../docs/15-production-ai-systems/prompt-caching.md)
- Also draws on: [circuit breakers](../../docs/06-production-reliability/circuit-breakers.md), [chat completion architecture](../../docs/14-ai-api-engineering/chat-completion-architecture.md), [streaming LLM responses](../../docs/14-ai-api-engineering/streaming-llm-responses.md)

## Requirements

- Single unified `POST /v1/chat/completions`-style endpoint that abstracts over at least two underlying providers with different native APIs.
- Each API key is issued to a tenant with its own model access list, token-per-minute and request-per-minute limits, and monthly budget cap.
- Model routing: a request can specify a logical model name (e.g. `"fast"`, `"smart"`) that the gateway maps to a concrete provider+model, or a specific provider/model directly.
- Automatic fallback: if the primary provider errors or times out, the gateway retries against a configured fallback provider/model transparently (when safe to do so — not for non-idempotent side effects).
- A circuit breaker per provider trips after repeated failures, temporarily routing all traffic away from a failing provider without waiting for every request to time out first.
- Token-bucket rate limiting enforced per API key, returning `429` with a `Retry-After` header when exceeded.
- Every request (success or failure) is logged with prompt/completion token counts and computed cost, aggregated per tenant per day.
- Streaming responses are supported end-to-end (gateway streams provider tokens through to the client without buffering the whole response).
- A budget cap: once a tenant exceeds its configured monthly spend, further requests are rejected with a clear error until the next billing cycle or a manual override.

## Architecture

```mermaid
flowchart LR
    Client[Client App] -->|API Key| Gateway[LLM Gateway]
    Gateway --> AuthN[API Key Auth + Tenant Lookup]
    Gateway --> RateLimiter[Token-Bucket Rate Limiter\n(per key, Redis)]
    Gateway --> Budget[Budget Enforcer]
    Gateway --> Router[Model Router\n(logical -> provider+model)]
    Router --> CB1[Circuit Breaker: Provider A]
    Router --> CB2[Circuit Breaker: Provider B]
    CB1 --> ProviderA[Provider A Client\n(OpenAI)]
    CB2 --> ProviderB[Provider B Client\n(Anthropic)]
    CB1 -.fallback on failure.-> CB2
    ProviderA --> UsageLog[(usage_logs — tokens, cost)]
    ProviderB --> UsageLog
    Gateway --> Client
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/v1/chat/completions` | Unified chat completion endpoint. Body includes `model` (logical or explicit), `messages`, `stream`. Supports SSE streaming. |
| POST | `/v1/embeddings` | Unified embeddings endpoint, routed the same way as chat completions. |
| GET | `/v1/models` | List logical model names available to the caller's API key and what they map to. |
| POST | `/keys` | (Admin) Create a new API key for a tenant with rate limits and budget cap. |
| GET | `/keys/{id}/usage` | Usage report for a key: requests, tokens, cost, broken down by day and by provider. |
| PATCH | `/keys/{id}` | Update a key's rate limits, budget cap, or allowed models. |
| DELETE | `/keys/{id}` | Revoke an API key immediately. |
| GET | `/admin/providers/status` | Current circuit-breaker state and recent error rate per provider. |

## Database Schema

```sql
CREATE TABLE tenants (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL,
    monthly_budget_usd NUMERIC(10,2) NOT NULL DEFAULT 100.00,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE api_keys (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash       TEXT UNIQUE NOT NULL,
    allowed_models TEXT[] NOT NULL DEFAULT '{"fast","smart"}',
    rpm_limit      INTEGER NOT NULL DEFAULT 60,
    tpm_limit      INTEGER NOT NULL DEFAULT 100000,
    status         TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE model_routes (
    logical_name   TEXT PRIMARY KEY,          -- e.g. 'fast', 'smart'
    provider       TEXT NOT NULL,             -- 'openai', 'anthropic', 'local'
    model_name     TEXT NOT NULL,             -- provider's actual model id
    fallback_provider TEXT,
    fallback_model TEXT,
    priority       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE usage_logs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenants(id),
    api_key_id     UUID NOT NULL REFERENCES api_keys(id),
    logical_model  TEXT NOT NULL,
    provider_used  TEXT NOT NULL,
    model_used     TEXT NOT NULL,
    was_fallback   BOOLEAN NOT NULL DEFAULT false,
    prompt_tokens  INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    cost_usd       NUMERIC(10,6) NOT NULL,
    latency_ms     INTEGER NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('success','error','rate_limited','budget_exceeded')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_tenant_day ON usage_logs (tenant_id, (created_at::date));
```

## Suggested Folder Structure

```
08-llm-gateway/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── completions.py
│   │   ├── embeddings.py
│   │   ├── keys.py
│   │   └── admin.py
│   ├── auth/
│   │   └── api_key_auth.py
│   ├── routing/
│   │   ├── model_router.py
│   │   └── config.py            # logical model -> provider mapping
│   ├── providers/
│   │   ├── base.py              # common provider interface
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   └── local_client.py
│   ├── reliability/
│   │   ├── circuit_breaker.py
│   │   └── fallback.py
│   ├── ratelimit/
│   │   └── token_bucket.py       # Redis-backed, per key
│   ├── billing/
│   │   ├── cost_calculator.py
│   │   └── budget_enforcer.py
│   ├── models/
│   │   ├── tenant.py
│   │   ├── api_key.py
│   │   └── usage_log.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_routing_and_fallback.py
│   ├── test_rate_limiting.py
│   ├── test_circuit_breaker.py
│   ├── test_budget_enforcement.py
│   └── test_streaming_passthrough.py
├── requirements.txt
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold FastAPI project, Postgres for `tenants`/`api_keys`/`usage_logs`, Redis for rate limiting and circuit breaker state.
2. Define the common `ProviderClient` interface (`complete(messages, model, stream) -> Response`) and implement it for two real providers, per [multi-provider architecture](../../docs/15-production-ai-systems/multi-provider-architecture.md).
3. Implement API key authentication: hash-lookup incoming keys, resolve tenant, attach `allowed_models`/limits to the request context.
4. Implement the `model_routes` table and router: map a logical model name to a concrete provider+model, and read a configured fallback pair, per [model routing](../../docs/15-production-ai-systems/model-routing.md).
5. Implement token-bucket rate limiting in Redis keyed by API key (both RPM and TPM buckets), returning 429 with `Retry-After` on exhaustion, per [token rate limits](../../docs/15-production-ai-systems/token-rate-limits.md).
6. Implement the cost calculator: a static per-provider/per-model price table (input/output token rates) used to compute `cost_usd` for every completed request.
7. Implement the budget enforcer: before routing, check the tenant's month-to-date spend against `monthly_budget_usd`; reject with a clear error if exceeded.
8. Implement `POST /v1/chat/completions` end to end: authenticate → rate limit → budget check → route → call provider → log usage → return response.
9. Implement the circuit breaker per provider (closed/open/half-open states) wrapping each provider client call, per [circuit breakers](../../docs/06-production-reliability/circuit-breakers.md).
10. Implement fallback: on a provider error or an open circuit breaker, transparently retry against the configured fallback provider/model, marking `was_fallback=true` in the usage log.
11. Implement streaming: proxy the provider's SSE/streaming response through to the client token-by-token without buffering, and only finalize the usage log once the stream completes (or is cancelled), per [streaming LLM responses](../../docs/14-ai-api-engineering/streaming-llm-responses.md).
12. Build `GET /keys/{id}/usage` aggregating `usage_logs` by day/provider, and `GET /admin/providers/status` exposing live circuit-breaker state.
13. Write tests that simulate a provider outage (mock client raises/times out) and assert the gateway falls back correctly and the circuit opens after N consecutive failures.

## Advanced Improvements

- Add prompt caching for repeated system prompts/prefixes to cut cost and latency, per [prompt caching](../../docs/15-production-ai-systems/prompt-caching.md).
- Add semantic caching across similar (not just identical) prompts, per [semantic caching](../../docs/15-production-ai-systems/semantic-caching.md).
- Add weighted/canary routing (e.g. 5% of "smart" traffic to a new model version) for safe rollout.
- Add per-tenant custom routing rules (e.g. a tenant that must never send data to a particular provider for compliance reasons).
- Add real-time budget alerts (webhook or email at 80%/100% of monthly budget).
- Add request/response logging with configurable redaction for sensitive prompt content.

## Production Checklist

- [ ] API keys stored as hashes, never logged or returned after creation.
- [ ] Rate limiting and budget checks happen before the (expensive) provider call, not after.
- [ ] Circuit breakers configured with sane thresholds and half-open probing so a recovered provider is detected automatically, per [circuit breakers](../../docs/06-production-reliability/circuit-breakers.md).
- [ ] Fallback logic only applies to safe-to-retry request types (avoid double side effects on function/tool-calling requests with external effects).
- [ ] Cost calculation kept in sync with providers' actual pricing (versioned price table, reviewed on provider price changes).
- [ ] Full observability: per-provider latency, error rate, and cost dashboards, per [AI observability](../../docs/15-production-ai-systems/ai-observability.md).
- [ ] Streaming responses handle client disconnects without leaving the upstream provider call running forever.
- [ ] Secrets (provider API keys) stored in a secrets manager, scoped least-privilege, rotatable without downtime.
- [ ] Load tested for target RPS with realistic provider latency simulated, including fallback paths.
- [ ] Runbook documented for "provider X is down" — expected gateway behavior, alerting, and manual override steps.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Pairs with: [Project 7 — Production RAG API](../07-production-rag/README.md), [Project 9 — AI Agent API](../09-ai-agent-api/README.md)
