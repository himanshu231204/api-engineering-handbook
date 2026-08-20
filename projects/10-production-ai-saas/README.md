# Project 10 — Complete Production AI SaaS Backend

## Goal

This is the capstone-of-capstones: a multi-tenant AI SaaS backend that combines everything you've built in Projects 1–9 into one coherent, deployable system. You will stand up authentication and multi-tenancy, an AI feature (RAG or an agent) behind an internal LLM gateway, usage-based billing, and the full production architecture described in Part 18 — API gateway, background workers, caching, object storage, message queues, and an observability stack. The point of this project is not to write new algorithms; it's to integrate previously-built pieces into a system that could plausibly run in production, with the operational concerns (multi-tenancy isolation, metering, rate limiting, observability, deploy safety) treated as first-class requirements rather than afterthoughts. If you build this end to end and can defend every design decision, you have genuinely completed the handbook.

## Builds On

- Everything: [Part 1 — API Foundations](../../docs/01-api-foundations/README.md) through [Part 19 — System Design Case Studies](../../docs/19-system-design-case-studies/README.md)
- Most directly:
  - [Part 5 — Authentication & Authorization](../../docs/05-authentication-authorization/README.md) (multi-tenant auth, RBAC)
  - [Part 6 — Production API Reliability](../../docs/06-production-reliability/README.md) (rate limiting, circuit breakers, graceful degradation)
  - [Part 7 — Caching & Performance](../../docs/07-caching-performance/README.md) (Redis, cache-aside)
  - [Part 8 — Async Systems](../../docs/08-async-systems/README.md) (background workers, queues)
  - [Part 12 — Observability](../../docs/12-observability/README.md) (logging, metrics, tracing, SLIs/SLOs)
  - [Part 15 — Production AI Systems](../../docs/15-production-ai-systems/README.md) (LLM gateway, cost tracking)
  - [Part 18 — Production Architecture](../../docs/18-production-architecture/README.md) (the reference architecture this project implements)
- Reuses whole subsystems from: [Project 2 — Authentication Service](../02-authentication-service/README.md), [Project 7 — Production RAG API](../07-production-rag/README.md) or [Project 9 — AI Agent API](../09-ai-agent-api/README.md), [Project 8 — Multi-Provider LLM Gateway](../08-llm-gateway/README.md)

## Requirements

- Multi-tenant from the ground up: every table, query, and cache key is scoped by `tenant_id`; no data ever leaks across tenants, including in the AI feature's retrieval/context.
- Authentication service (Project 2) issues tokens; every downstream service validates them without re-implementing auth logic.
- One AI product feature — either the RAG pipeline (Project 7) or the agent API (Project 9) — fully wired into the SaaS, gated by tenant plan/entitlements.
- All LLM calls route through the internal gateway (Project 8) so routing, fallback, and cost tracking are centralized, not duplicated per feature.
- Usage-based billing: every metered action (API request, tokens consumed, documents ingested, agent runs) is recorded and rolled up into a per-tenant usage report and a monthly invoice-style summary.
- Plan enforcement: tenants on a given plan (e.g. Free/Pro/Enterprise) have different rate limits, feature access, and usage caps, enforced server-side.
- Redis-backed caching for expensive, frequently-repeated reads (e.g. tenant/plan lookups, model routing config).
- Background workers handle all long-running work (document ingestion, billing rollups, webhook delivery) via a message queue, never inline in a request handler.
- Full observability: structured logs with request IDs, metrics (latency, error rate, cost), and distributed tracing across the API gateway → services → workers → LLM gateway call chain.
- A documented, testable deploy story: health/readiness probes, environment-based configuration, and a rollback plan.

## Architecture

```mermaid
flowchart TB
    Client[Client / SPA / Mobile] --> Gateway[API Gateway\n(routing, authN, rate limiting)]
    Gateway --> Auth[Auth Service\n(Project 2)]
    Gateway --> AppAPI[Application API\n(tenants, billing, feature routes)]
    Gateway --> AIFeature[AI Feature Service\nRAG (Project 7) or Agent (Project 9)]

    AIFeature --> LLMGateway[Internal LLM Gateway\n(Project 8)]
    LLMGateway --> ProviderA[Provider A]
    LLMGateway --> ProviderB[Provider B]

    AppAPI --> Redis[(Redis\ncache + rate limits)]
    AIFeature --> Redis
    AppAPI --> Postgres[(PostgreSQL\ntenants, users, usage, billing)]
    AIFeature --> VectorDB[(pgvector / Vector Store)]

    AppAPI --> Queue[(Message Queue)]
    Queue --> Workers[Background Workers\ningestion, billing rollup, webhook delivery]
    Workers --> ObjectStorage[(Object Storage\ndocuments, exports)]

    AppAPI --> Webhooks[Outbound Webhook System\n(Project 4 pattern)]

    subgraph Observability Stack
        Logs[Structured Logs]
        Metrics[Metrics]
        Tracing[Distributed Tracing]
    end

    Gateway -.-> Observability Stack
    AppAPI -.-> Observability Stack
    AIFeature -.-> Observability Stack
    Workers -.-> Observability Stack
    LLMGateway -.-> Observability Stack
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | Delegated to the Auth Service (Project 2); the gateway validates tokens on every downstream call. |
| POST | `/tenants` | Create a new tenant (organization) and its owner user. |
| GET | `/tenants/{id}` | Tenant profile, current plan, and entitlements. |
| PATCH | `/tenants/{id}/plan` | Change a tenant's plan (Free/Pro/Enterprise); updates rate limits/feature flags. |
| GET | `/tenants/{id}/usage` | Usage report: requests, tokens, documents, agent runs, current-period cost — for billing UI. |
| GET | `/tenants/{id}/invoices` | Historical monthly invoice-style usage summaries. |
| POST | `/documents` / `POST /agents/{id}/runs` | The AI feature's endpoints from Project 7 or Project 9, now gated by tenant plan and metered. |
| GET | `/query` (RAG) or `/runs/{id}` (Agent) | Feature-specific read endpoints, unchanged from the source project but tenant-scoped. |
| POST | `/webhooks/subscriptions` | Tenants register outbound webhooks for events like `usage.threshold_reached`, `invoice.generated` (Project 4 pattern). |
| GET | `/admin/tenants` | Internal admin: list all tenants, plan distribution, top usage/cost. |
| GET | `/health`, `/ready` | Liveness/readiness probes for every service in the system. |

## Database Schema

```sql
CREATE TABLE tenants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    plan                TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free','pro','enterprise')),
    status              TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email               TEXT NOT NULL,
    role                TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner','admin','member')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

CREATE TABLE plans (
    plan_name           TEXT PRIMARY KEY,
    rpm_limit           INTEGER NOT NULL,
    tpm_limit           INTEGER NOT NULL,
    monthly_budget_usd  NUMERIC(10,2) NOT NULL,
    max_documents       INTEGER,
    max_agent_runs      INTEGER,
    included_seats      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE usage_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    user_id             UUID,
    event_type          TEXT NOT NULL,      -- 'api_request','llm_tokens','document_ingested','agent_run'
    quantity             NUMERIC(12,4) NOT NULL,
    cost_usd            NUMERIC(10,6) NOT NULL DEFAULT 0,
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_events_tenant_day ON usage_events (tenant_id, (created_at::date));

CREATE TABLE invoices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    period_start        DATE NOT NULL,
    period_end          DATE NOT NULL,
    total_cost_usd      NUMERIC(10,2) NOT NULL,
    status              TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','finalized','paid')),
    generated_at        TIMESTAMPTZ,
    UNIQUE (tenant_id, period_start, period_end)
);

-- Reused from Project 2: users, refresh_tokens (auth service, keyed by tenant_id)
-- Reused from Project 7 or 9: documents/chunks or agents/runs/steps (all now carrying tenant_id)
-- Reused from Project 8: api_keys, model_routes, usage_logs (as the internal LLM gateway's own tables)
-- Reused from Project 4 pattern: subscriptions, deliveries (for tenant-facing outbound webhooks)
```

## Suggested Folder Structure

```
10-production-ai-saas/
├── services/
│   ├── gateway/                  # API gateway: routing, authN passthrough, global rate limiting
│   │   └── app/
│   ├── auth-service/             # = Project 2, reused as-is
│   ├── app-api/                  # tenants, users, billing, plan enforcement
│   │   └── app/
│   │       ├── api/routes/
│   │       │   ├── tenants.py
│   │       │   ├── usage.py
│   │       │   └── invoices.py
│   │       ├── services/
│   │       │   ├── entitlement_service.py
│   │       │   ├── usage_metering.py
│   │       │   └── billing_rollup.py
│   │       ├── models/
│   │       └── db/
│   ├── ai-feature/                # = Project 7 (RAG) or Project 9 (Agent), tenant-scoped
│   ├── llm-gateway/               # = Project 8, reused as internal-only service
│   ├── webhook-system/            # = Project 4 pattern, tenant-facing outbound webhooks
│   └── workers/
│       ├── ingestion_worker.py
│       ├── billing_rollup_worker.py
│       └── webhook_delivery_worker.py
├── infra/
│   ├── docker-compose.yml         # all services + postgres + redis + queue
│   ├── k8s/                       # optional: manifests for each service
│   └── observability/
│       ├── otel-collector-config.yaml
│       └── dashboards/
├── shared/
│   ├── auth_client.py             # shared JWT verification used by every service
│   ├── tracing.py                 # shared OpenTelemetry setup
│   └── tenant_context.py          # tenant_id propagation middleware
├── tests/
│   ├── test_tenant_isolation.py
│   ├── test_plan_enforcement.py
│   ├── test_usage_metering_accuracy.py
│   └── test_end_to_end_flow.py
└── README.md
```

## Step-by-Step Implementation Plan

1. Stand up the `tenants`, `users`, and `plans` tables and a tenant-provisioning flow (`POST /tenants` creates a tenant + owner user), building on [Project 2's](../02-authentication-service/README.md) user model extended with `tenant_id`.
2. Deploy the Auth Service (Project 2) as its own service; add `tenant_id` to its JWT claims so every downstream service can extract tenant context from the token alone.
3. Build a shared `tenant_context` middleware/dependency used by every service to enforce that all DB queries and cache keys are scoped by `tenant_id` — write this once, reuse everywhere.
4. Stand up the API Gateway layer: request routing to the right internal service, global authentication check, and coarse-grained rate limiting, per [API Gateway](../../docs/11-microservices-distributed-systems/api-gateway.md) and [Part 18's reference architecture](../../docs/18-production-architecture/README.md).
5. Deploy the LLM Gateway (Project 8) as an internal-only service; the AI feature calls it instead of any provider directly, so cost tracking and fallback are centralized.
6. Deploy the AI feature — RAG (Project 7) or Agent (Project 9) — adding `tenant_id` scoping to every ingestion, retrieval, and run record, and writing an explicit test that proves cross-tenant retrieval is impossible.
7. Implement plan-based entitlement checks (`entitlement_service.py`): before serving a metered feature, check the tenant's plan limits (max documents, max agent runs, RPM/TPM) and reject with a clear 402/429 when exceeded.
8. Implement usage metering: every metered action writes a `usage_events` row (API request, LLM tokens via the gateway's own `usage_logs`, document ingested, agent run) — prefer writing usage events asynchronously via the queue so metering never blocks the request path.
9. Implement Redis caching for tenant/plan lookups (cache-aside, short TTL, explicit invalidation on plan change) per [cache-aside](../../docs/07-caching-performance/cache-aside.md) and [cache invalidation](../../docs/07-caching-performance/cache-invalidation.md).
10. Build the background workers: ingestion worker (reuses Project 5/7's pattern), a scheduled billing rollup worker that aggregates `usage_events` into `invoices` at period end, and the webhook delivery worker (Project 4 pattern) for tenant-facing events like `usage.threshold_reached`.
11. Wire up the message queue connecting the app API to the workers so nothing long-running happens synchronously inside a request handler, per [message queues](../../docs/08-async-systems/message-queues.md).
12. Add the observability stack: structured JSON logging with a propagated `request_id`/`trace_id` across every service hop, per-service metrics (latency, error rate, cost), and distributed tracing through the full chain (gateway → app API → AI feature → LLM gateway → provider), per [distributed tracing](../../docs/12-observability/distributed-tracing.md).
13. Define SLIs/SLOs for the system (e.g. p95 API latency, RAG answer latency, ingestion completion time) per [SLI, SLO, SLA](../../docs/12-observability/sli-slo-sla.md), and build a dashboard against them.
14. Add `/health` and `/ready` probes to every service, wire graceful shutdown, and document a rollback plan for a bad deploy.
15. Write an end-to-end test suite: provision a tenant, hit its plan limits, ingest a document or run an agent, verify usage events and an invoice roll up correctly, and confirm a second tenant can never see the first tenant's data.

## Advanced Improvements

- Add real payment processing (Stripe-style) reusing the idempotent-charge pattern from [Project 3](../03-payment-api/README.md) to actually bill tenants for their invoices.
- Add per-tenant custom LLM routing rules (e.g. an Enterprise tenant pinned to a specific provider for compliance) via the gateway's routing config.
- Add a self-serve admin dashboard for tenant owners to see usage, manage seats, and view invoices.
- Add horizontal autoscaling for the AI feature and worker services based on queue depth and request rate.
- Add chaos testing (kill a provider, kill a worker mid-job) to validate the system degrades gracefully instead of losing data, per [chaos testing basics](../../docs/13-api-testing/README.md).
- Add a data export/deletion flow per tenant for compliance (GDPR-style "right to be forgotten").

## Production Checklist

- [ ] Tenant isolation is enforced at the query layer everywhere (row-level `tenant_id` filters, never trusted from client input alone) and explicitly tested for leakage.
- [ ] Every metered action reliably produces exactly one usage event — audited against provider-reported LLM token usage for drift, reusing the reconciliation idea from [Project 3](../03-payment-api/README.md).
- [ ] Plan/entitlement checks happen before expensive work starts, not after, to avoid wasted spend on rejected requests.
- [ ] Full request tracing across service boundaries with correlation IDs, so a slow or failed request can be diagnosed end to end.
- [ ] Rate limiting enforced at both the gateway (coarse, per-tenant) and the LLM gateway (fine-grained, per-key) layers.
- [ ] Secrets (DB credentials, provider keys, signing keys) managed centrally and never duplicated in per-service `.env` files in production.
- [ ] Health/readiness probes on every service wired into the deploy pipeline so a bad deploy is caught before traffic shifts.
- [ ] Billing rollups are idempotent and re-runnable without double-charging or double-counting usage.
- [ ] Load and failure testing: a single provider outage, a worker crash, or a Redis outage degrades gracefully rather than cascading into a full outage, per [graceful degradation](../../docs/06-production-reliability/README.md) and [circuit breakers](../../docs/06-production-reliability/circuit-breakers.md).
- [ ] Documented runbooks for the top 3 likely incidents (provider outage, queue backlog, tenant over quota) with clear on-call actions.
- [ ] Automated test suite covering tenant isolation, plan enforcement, and the full ingest-or-agent-run-to-invoice flow, running in CI on every change.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Integrates: [Project 2 — Authentication Service](../02-authentication-service/README.md), [Project 4 — Webhook Processing System](../04-webhook-system/README.md), [Project 7 — Production RAG API](../07-production-rag/README.md), [Project 8 — Multi-Provider LLM Gateway](../08-llm-gateway/README.md), [Project 9 — AI Agent API](../09-ai-agent-api/README.md)
- System design counterparts: [Design a Multi-Tenant AI SaaS](../../docs/19-system-design-case-studies/README.md), [Design an LLM Gateway](../../docs/19-system-design-case-studies/README.md)
