# Webhooks Cheatsheet

For the full explanation, see [Real-Time APIs & Webhooks](../../docs/09-realtime-and-webhooks/README.md).

## Signature verification checklist (receiving a webhook)

- [ ] Read the **raw request body bytes** before any JSON parsing — signatures are computed over the raw bytes, and re-serializing JSON can change whitespace/key order and break verification.
- [ ] Extract the signature from the header the provider sends (e.g. `Stripe-Signature`, `X-Hub-Signature-256`).
- [ ] Extract the timestamp if the provider includes one in the signed payload.
- [ ] Recompute the HMAC (usually HMAC-SHA256) over `timestamp + "." + raw_body` (or provider-specific format) using your **webhook signing secret**.
- [ ] Compare your computed signature to the received signature using a **constant-time comparison** (never `==`/`string.Equals` — timing attacks can leak the secret byte-by-byte).
- [ ] Reject the request if the timestamp is outside an acceptable window (e.g. 5 minutes) to prevent replay attacks.
- [ ] Return `2xx` only after verification succeeds; return `401`/`400` on signature mismatch.
- [ ] Store and rotate the signing secret like any other credential — never log it.

## Retry / backoff quick reference (sending webhooks)

- Most providers retry failed webhook deliveries (non-2xx response, or timeout) with **exponential backoff**, often over a long window (minutes to days).
- Typical pattern: retry at 1min, 5min, 30min, 2hr, 12hr, 24hr... with a cap (e.g. stop after 3–5 days).
- Respond fast (`< 5s`, ideally `< 1s`) and with `200`/`202` immediately — do the actual processing asynchronously (queue it). Slow handlers cause providers to time out and retry, creating duplicate work.
- Expose delivery history/retry status if you're the sender — consumers will ask "did my webhook get delivered?"
- Always include a unique event ID in the payload so the receiver can deduplicate.

## Idempotent consumer checklist

- [ ] Every incoming webhook event has a unique ID (from the provider, e.g. `evt_...`).
- [ ] Before processing, check if this event ID has already been processed (DB lookup on a `processed_events` table, or a dedup cache with TTL longer than the provider's retry window).
- [ ] If already processed, return `200 OK` immediately without reprocessing (this is what lets retries be safe).
- [ ] Processing an event is wrapped so recording "this event was processed" happens atomically with the side effect (e.g. same DB transaction) — otherwise a crash between the two can cause double-processing or silent drops.
- [ ] Design side effects to be idempotent themselves where possible (e.g. `UPSERT` instead of `INSERT`, "set status to X" instead of "increment by 1").
- [ ] Handle out-of-order delivery — don't assume events arrive in the order they were generated; use event timestamps/sequence numbers to detect and handle out-of-order updates.
- [ ] Log/alert on repeated failures for the same event so you catch a poison-pill event instead of retrying it forever.

## Common mistakes

- Verifying the signature against the parsed/re-serialized JSON instead of the raw body bytes.
- Doing slow synchronous work (calling other APIs, heavy DB writes) inside the webhook handler before responding.
- Not deduplicating — assuming "at-least-once" delivery means "exactly-once."
- Trusting the payload's own claims about its origin instead of verifying the signature.
- Not handling the case where your endpoint is down for a while and a backlog of retried webhooks arrives all at once.
