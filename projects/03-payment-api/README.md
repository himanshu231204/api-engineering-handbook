# Project 3 — E-commerce Order + Payment API

## Goal

Build an order and payment API that models a real e-commerce checkout flow: cart → order → payment → fulfillment. This project's entire point is to make idempotency, state machines, and asynchronous confirmation feel real instead of theoretical — money is the domain where "just retry it" or "just re-run the request" can silently double-charge a customer if you get it wrong. You'll implement an idempotent charge endpoint, a webhook receiver for asynchronous payment confirmation (simulating a provider like Stripe), and an append-only ledger so every balance is always reconstructable from history.

## Builds On

- [Part 4 — Databases & APIs](../../docs/04-databases-and-apis/README.md)
- [Part 6 — Production API Reliability](../../docs/06-production-reliability/README.md)
- Specifically: [database transactions](../../docs/04-databases-and-apis/README.md), [idempotency](../../docs/02-rest-api-design/idempotency.md), [timeouts](../../docs/06-production-reliability/timeouts.md), [retries](../../docs/06-production-reliability/retries.md), [exponential backoff](../../docs/06-production-reliability/exponential-backoff.md)
- Optional: [webhook signature verification](../../docs/09-realtime-and-webhooks/webhook-signature-verification.md) for the payment-provider webhook
- Recommended pairing: [Project 2 — Authentication Service](../02-authentication-service/README.md) for user identity

## Requirements

- Users can add items to a cart, then convert the cart into an order (immutable snapshot of items/prices at order time).
- `POST /orders/{id}/charge` is idempotent: a client-supplied `Idempotency-Key` header guarantees the same request, retried any number of times, produces exactly one charge.
- Orders move through a strict state machine: `pending` → `payment_processing` → `paid` → `shipped` → `delivered`, with `cancelled` and `refunded` as terminal side-branches from applicable states.
- Payment confirmation is asynchronous: the charge endpoint returns immediately with `payment_processing`, and a simulated payment provider later calls a webhook to confirm or fail the payment.
- Webhook receiver verifies a signature header before trusting the payload (simulate HMAC signing, as a real provider like Stripe would do).
- An append-only ledger table records every money-moving event (charge attempt, charge success, refund) — account balances/order totals are derived from the ledger, never mutated directly.
- Illegal state transitions (e.g., shipping an unpaid order, refunding a pending order) are rejected with 409 Conflict.
- Refunds are supported and themselves idempotent.

## Architecture

```mermaid
flowchart LR
    Client[Client] -->|create cart / order| API[Order API]
    API --> OrderSvc[Order Service\n(state machine)]
    Client -->|POST /orders/id/charge\nIdempotency-Key| API
    API --> IdemStore[(Idempotency Key Store)]
    API --> PaySvc[Payment Service]
    PaySvc -->|charge request| Provider[Simulated Payment Provider]
    Provider -->|async webhook: payment.succeeded/failed| Webhook[Webhook Receiver]
    Webhook --> SigVerify[Signature Verification]
    Webhook --> OrderSvc
    OrderSvc --> DB[(orders, order_items)]
    PaySvc --> Ledger[(ledger — append only)]
    OrderSvc --> DB
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/cart/items` | Add an item (product_id, quantity) to the current user's cart. |
| GET | `/cart` | View current cart contents and computed total. |
| DELETE | `/cart/items/{item_id}` | Remove an item from the cart. |
| POST | `/orders` | Convert the current cart into an order (snapshot prices, set state `pending`). |
| GET | `/orders/{order_id}` | Get order details and current state. |
| GET | `/orders` | List the authenticated user's orders, paginated. |
| POST | `/orders/{order_id}/charge` | Initiate payment. Requires `Idempotency-Key` header. Returns `payment_processing`. |
| POST | `/webhooks/payment-provider` | Receiver for async payment confirmation events. Verifies HMAC signature. |
| POST | `/orders/{order_id}/refund` | Request a refund for a paid order. Idempotent per `Idempotency-Key`. |
| POST | `/orders/{order_id}/ship` | Mark an order shipped (internal/admin use — only legal from `paid`). |
| GET | `/orders/{order_id}/ledger` | View the append-only ledger entries for an order (audit trail). |

## Database Schema

```sql
CREATE TABLE orders (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','payment_processing','paid','shipped','delivered','cancelled','refunded')),
    total_cents    INTEGER NOT NULL CHECK (total_cents >= 0),
    currency       TEXT NOT NULL DEFAULT 'USD',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id       UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id     UUID NOT NULL,
    product_name   TEXT NOT NULL,       -- snapshot, not a live join
    unit_price_cents INTEGER NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE TABLE idempotency_keys (
    key            TEXT PRIMARY KEY,
    order_id       UUID NOT NULL REFERENCES orders(id),
    request_hash   TEXT NOT NULL,       -- hash of request body, to detect key reuse with different payload
    response_body  JSONB,
    response_status INTEGER,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ledger_entries (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id       UUID NOT NULL REFERENCES orders(id),
    entry_type     TEXT NOT NULL CHECK (entry_type IN ('charge_attempt','charge_succeeded','charge_failed','refund')),
    amount_cents   INTEGER NOT NULL,
    provider_ref   TEXT,                -- external payment provider's transaction id
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE webhook_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_event_id TEXT UNIQUE NOT NULL,   -- dedupe key for redelivered webhooks
    payload        JSONB NOT NULL,
    processed_at   TIMESTAMPTZ,
    received_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Suggested Folder Structure

```
03-payment-api/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── cart.py
│   │   ├── orders.py
│   │   └── webhooks.py
│   ├── schemas/
│   │   ├── order.py
│   │   └── payment.py
│   ├── services/
│   │   ├── order_service.py       # state machine transitions
│   │   ├── payment_service.py
│   │   └── idempotency_service.py
│   ├── providers/
│   │   └── mock_payment_provider.py
│   ├── models/
│   │   ├── order.py
│   │   ├── ledger.py
│   │   └── idempotency.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_idempotent_charge.py
│   ├── test_state_machine.py
│   ├── test_webhook_signature.py
│   └── test_refund.py
├── requirements.txt
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold FastAPI + Postgres project; define `orders`, `order_items`, `ledger_entries` tables and migrations.
2. Implement the cart (can be in-memory/session-scoped or a simple `cart_items` table) and `POST /orders` to snapshot it into an immutable order.
3. Design the order state machine as an explicit function/class (`allowed_transitions: dict[state, set[state]]`) so illegal transitions are rejected in one place, not scattered across endpoints.
4. Build the `idempotency_keys` table and a reusable `idempotency` dependency/middleware: on a repeated key with the same request hash, return the stored response without re-executing side effects; on a repeated key with a different payload, return 409/422.
5. Implement `POST /orders/{id}/charge`: validate state is `pending`, write a `charge_attempt` ledger entry, call the mock payment provider, transition order to `payment_processing`, return immediately.
6. Build the `MockPaymentProvider`: simulates network latency and asynchronously (background task or delayed call) fires a signed webhook back to your own `/webhooks/payment-provider` endpoint with a success/failure event.
7. Implement webhook signature verification (HMAC-SHA256 over the raw body with a shared secret) before trusting any webhook payload, per [webhook signature verification](../../docs/09-realtime-and-webhooks/webhook-signature-verification.md).
8. Implement webhook event deduplication using `webhook_events.provider_event_id` so redelivered webhooks (which providers do on purpose) don't double-apply.
9. On a verified `payment.succeeded` event, transition the order `payment_processing` → `paid` and write a `charge_succeeded` ledger entry inside one DB transaction.
10. On `payment.failed`, transition back to `pending` (or a `payment_failed` state) so the user can retry, and record `charge_failed`.
11. Implement `POST /orders/{id}/refund` following the same idempotency-key + ledger pattern, only legal from `paid`/`shipped`.
12. Write tests that specifically hammer the idempotency logic: fire the same charge request twice concurrently and assert only one ledger `charge_attempt` exists.

## Advanced Improvements

- Add partial refunds and partial shipment support.
- Add a scheduled reconciliation job that compares your ledger totals against the (mock) provider's reported totals and alerts on drift.
- Add exponential backoff with jitter when calling the payment provider, per [exponential backoff](../../docs/06-production-reliability/exponential-backoff.md).
- Add a dead-letter mechanism for webhooks that fail signature verification or processing repeatedly.
- Model multi-currency orders with a stored exchange rate at order time.
- Add a circuit breaker around the payment provider client so a provider outage degrades gracefully instead of hanging every checkout.

## Production Checklist

- [ ] Every money-moving endpoint requires and enforces `Idempotency-Key`; keys are scoped per user/order to prevent cross-account replay.
- [ ] All ledger writes and state transitions happen inside a single database transaction (no partial updates on crash).
- [ ] Webhook signature verification uses constant-time comparison and rejects payloads with a stale timestamp (replay protection).
- [ ] Webhook events are deduplicated by provider event ID before any processing occurs.
- [ ] No real card data ever touches your servers — this is a hard PCI-DSS scope boundary; charges are delegated to a provider/mock, never processed in-house.
- [ ] Order state machine transitions are centrally defined and unit-tested for every illegal transition, not just the happy path.
- [ ] Monetary amounts stored as integer cents, never floats.
- [ ] Alerting on ledger/provider reconciliation drift above a defined threshold.
- [ ] Rate limiting on the charge endpoint to blunt card-testing/fraud attempts.
- [ ] Full audit trail (ledger + webhook_events) retained and queryable for dispute resolution.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Pairs with: [Project 2 — Authentication Service](../02-authentication-service/README.md)
