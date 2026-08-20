"""
Webhook RECEIVER: verifies an inbound HMAC-SHA256 signature before trusting
any payload.

Implements exactly the scheme described in
docs/09-realtime-and-webhooks/webhook-signature-verification.md: a
`X-Signature: t=<unix-ts>,v1=<hex-hmac>` header, timing-safe comparison via
`hmac.compare_digest`, and a replay-protection window on the timestamp.
Pairs with sender.py, which signs payloads in this exact format.

Run it:
    export WEBHOOK_SECRET=dev-secret-change-me
    uvicorn receiver:app --reload
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

load_dotenv()

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise RuntimeError(
        "WEBHOOK_SECRET environment variable is required. Copy .env.example to "
        ".env and set it -- it must match sender.py's WEBHOOK_SECRET."
    )

REPLAY_TOLERANCE_SECONDS = int(os.environ.get("REPLAY_TOLERANCE_SECONDS", "300"))

app = FastAPI(title="Webhook Receiver Example", version="1.0.0")

# In-memory log of accepted events, purely so you can inspect what got
# through verification. Not a real persistence layer -- see
# examples/fastapi-crud for that pattern.
received_events: list[dict] = []


def verify_webhook_signature(raw_body: bytes, signature_header: str, secret: str) -> None:
    """Raises ValueError with a specific reason if verification fails.

    `signature_header` looks like: "t=1755511200,v1=5b3f8a1c...".
    """
    try:
        parts = dict(item.split("=", 1) for item in signature_header.split(","))
        timestamp = int(parts["t"])
        provided_signature = parts["v1"]
    except (KeyError, ValueError) as exc:
        raise ValueError("malformed_signature_header") from exc

    # Replay protection: reject requests signed too long ago (or too far in
    # the future -- clock skew aside, that's also suspicious).
    now = int(time.time())
    if abs(now - timestamp) > REPLAY_TOLERANCE_SECONDS:
        raise ValueError("stale_timestamp")

    # Recompute the expected signature over "{timestamp}.{raw_body}", using
    # the RAW bytes -- never a re-parsed/re-serialized version of the JSON.
    signed_payload = f"{timestamp}.".encode() + raw_body
    expected_signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()

    # Timing-safe comparison -- never use `==`/`!=` to compare signatures.
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise ValueError("signature_mismatch")


@app.post("/webhooks/incoming")
async def receive_webhook(request: Request, x_signature: str = Header(...)) -> dict:
    # Read RAW bytes for verification -- request.json() would re-parse the
    # body and could produce a different hash than what the sender signed.
    raw_body = await request.body()

    try:
        verify_webhook_signature(raw_body, x_signature, WEBHOOK_SECRET)
    except ValueError as exc:
        # Vague to the caller on purpose; the specific reason only goes to
        # server logs, so a would-be attacker can't use the error message
        # to iteratively probe the verification logic.
        print(f"[receiver] rejected webhook: {exc}")
        raise HTTPException(status_code=400, detail="signature_verification_failed") from exc

    event = await request.json()
    received_events.append(event)
    print(f"[receiver] accepted webhook: {event.get('type', '<no type>')}")
    return {"received": True}


@app.get("/webhooks/received", summary="Inspect accepted events so far (debug only)")
async def list_received_events() -> dict:
    return {"count": len(received_events), "events": received_events}
