# Webhooks — HMAC Signature Verification + Reliable Delivery

Accompanies [Part 9 — Real-Time APIs](../../docs/09-realtime-and-webhooks/README.md), especially
[Webhook Signature Verification](../../docs/09-realtime-and-webhooks/webhook-signature-verification.md)
and [Webhooks](../../docs/09-realtime-and-webhooks/webhooks.md). The retry logic also ties back to
[Part 6 — Production Reliability](../../docs/06-production-reliability/README.md): specifically
[Retries](../../docs/06-production-reliability/retries.md), and
[Exponential Backoff](../../docs/06-production-reliability/exponential-backoff.md) (a standalone Jitter chapter is planned).

## What this demonstrates

Two halves of a webhook integration, talking to each other:

- **`receiver.py`** — a FastAPI endpoint that verifies every inbound request's
  `X-Signature: t=<unix-ts>,v1=<hex-hmac>` header before trusting the payload: it
  recomputes `HMAC-SHA256(secret, "{timestamp}.{raw_body}")` over the **raw** request
  bytes, compares it with `hmac.compare_digest` (timing-safe — never `==`), and rejects
  requests whose timestamp is outside a tolerance window (replay protection).
- **`sender.py`** — signs a JSON payload the same way and POSTs it, retrying on
  connection errors and `5xx` responses with **exponential backoff + full jitter**, and
  giving up immediately (no retry) on a `4xx`, since resending byte-identical data to a
  receiver that already rejected it would just fail again.

Run both together and you'll see: a correctly signed request accepted, and a
tampered-after-signing request rejected — all from real HTTP calls between two
processes, not a unit test mocking anything away.

## Prerequisites

- Python 3.11+

## How to run it

Terminal 1 — start the receiver:

```bash
cd examples/webhooks
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# both receiver.py and sender.py read WEBHOOK_SECRET from this .env

uvicorn receiver:app --reload
```

Terminal 2 — run the sender:

```bash
cd examples/webhooks
source .venv/bin/activate
python sender.py
```

You should see the receiver log an accepted webhook, and the sender log a successful
`200`, followed by the tampered-payload attempt being rejected with a `400`.

Check what the receiver actually accepted:

```bash
curl http://127.0.0.1:8000/webhooks/received
```

## Try it

```bash
# Send a request with no signature header at all -- FastAPI itself
# rejects it (422, missing required header) before your code even runs.
curl -i -X POST http://127.0.0.1:8000/webhooks/incoming \
  -H "Content-Type: application/json" -d '{"id": "evt_1", "type": "test"}'

# Send a request with a garbage signature -- your verification code
# rejects it (400).
curl -i -X POST http://127.0.0.1:8000/webhooks/incoming \
  -H "Content-Type: application/json" \
  -H "X-Signature: t=1755511200,v1=deadbeef" \
  -d '{"id": "evt_1", "type": "test"}'
```

## Things to try

1. **Break the replay protection.** In `receiver.py`, set `REPLAY_TOLERANCE_SECONDS=5`,
   then in `sender.py`'s `sign_payload` call, pass a `timestamp` 30 seconds in the past —
   watch a *correctly signed* request get rejected purely for being stale. This is the
   check that stops a captured, perfectly valid request from being replayed hours later.
2. **Make the receiver briefly unavailable.** Stop the `uvicorn` process, run
   `python sender.py`, and watch it retry with growing delays before giving up — then
   restart the receiver mid-retry-loop and watch the next attempt succeed. This is the
   difference between a webhook system that loses events during a deploy and one that
   doesn't.
3. **Implement secret rotation.** The verification function in `receiver.py` checks
   against exactly one secret. Change it to accept a `WEBHOOK_SECRET_PREVIOUS` as well and
   accept a signature produced by *either* secret — this is what lets you rotate a leaked
   or expiring secret without rejecting in-flight webhooks signed just before the
   rotation (see the "Advanced" exercise in the signature-verification chapter).
