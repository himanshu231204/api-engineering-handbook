"""
Webhook SENDER: signs a payload the same way receiver.py expects, and POSTs
it with retry + exponential backoff (with jitter) on transient failure.

Uses only the standard library (`urllib`) so this has no dependency beyond
`python-dotenv`. See docs/06-production-reliability/retries.md,
docs/06-production-reliability/exponential-backoff.md, and
docs/06-production-reliability/jitter.md.

Run the receiver first:
    export WEBHOOK_SECRET=dev-secret-change-me
    uvicorn receiver:app --reload

Then, in another terminal:
    export WEBHOOK_SECRET=dev-secret-change-me
    python sender.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import random
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "http://127.0.0.1:8000/webhooks/incoming")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise RuntimeError(
        "WEBHOOK_SECRET environment variable is required (must match receiver.py's). "
        "See .env.example."
    )

MAX_ATTEMPTS = int(os.environ.get("WEBHOOK_MAX_ATTEMPTS", "5"))
BASE_DELAY_SECONDS = float(os.environ.get("WEBHOOK_BASE_DELAY_SECONDS", "0.5"))
MAX_DELAY_SECONDS = float(os.environ.get("WEBHOOK_MAX_DELAY_SECONDS", "10"))


def sign_payload(raw_body: bytes, secret: str, timestamp: int | None = None) -> str:
    """Returns a signature header value: "t=<unix-ts>,v1=<hex-hmac>"."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode() + raw_body
    digest = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def send_webhook(url: str, event: dict, secret: str) -> None:
    """POSTs `event`, retrying on failure with exponential backoff + full jitter.

    Retries on connection errors and 5xx responses (the receiver being
    temporarily down or overloaded). Does NOT retry on 4xx: a 400 means the
    receiver actively rejected the request (e.g. bad signature), and
    resending byte-for-identical data would just fail again identically.
    """
    raw_body = json.dumps(event).encode("utf-8")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Re-sign on every attempt with a fresh timestamp -- a signature
        # from several retries ago could fall outside the receiver's
        # replay-tolerance window by the time it's finally delivered.
        signature = sign_payload(raw_body, secret)
        request = UrlRequest(
            url,
            data=raw_body,
            method="POST",
            headers={"Content-Type": "application/json", "X-Signature": signature},
        )

        try:
            with urlopen(request, timeout=5) as response:
                print(f"[sender] attempt {attempt}: {response.status} {response.reason}")
                return
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if 400 <= exc.code < 500:
                print(f"[sender] attempt {attempt}: {exc.code} {exc.reason} -- {body} (client error, not retrying)")
                return
            print(f"[sender] attempt {attempt}: {exc.code} {exc.reason} -- {body} (will retry)")
        except URLError as exc:
            print(f"[sender] attempt {attempt}: connection error -- {exc.reason} (will retry)")

        if attempt < MAX_ATTEMPTS:
            # Exponential backoff: delay grows as base * 2^(attempt-1),
            # capped at MAX_DELAY_SECONDS. Full jitter (a random value
            # between 0 and the capped delay) avoids every retrying client
            # waking up at exactly the same instant and re-overwhelming a
            # recovering server -- see docs/06-production-reliability/jitter.md.
            capped_delay = min(BASE_DELAY_SECONDS * (2 ** (attempt - 1)), MAX_DELAY_SECONDS)
            delay = random.uniform(0, capped_delay)
            print(f"[sender] retrying in {delay:.2f}s...")
            time.sleep(delay)

    print(f"[sender] gave up after {MAX_ATTEMPTS} attempts")


def _demo_tampered_payload(url: str, event: dict, secret: str) -> None:
    """Signs one payload but sends a DIFFERENT one -- demonstrates that
    tampering after signing is caught, and that this is a 4xx (no retry)."""
    raw_body_signed = json.dumps(event).encode("utf-8")
    signature = sign_payload(raw_body_signed, secret)

    tampered_event = dict(event, data={**event["data"], "amount": 999_999})
    request = UrlRequest(
        url,
        data=json.dumps(tampered_event).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-Signature": signature},
    )
    try:
        with urlopen(request, timeout=5) as response:
            print(f"[sender] unexpected success: {response.status} (tampering should have been caught!)")
    except HTTPError as exc:
        print(f"[sender] rejected as expected: {exc.code} {exc.read().decode('utf-8', errors='replace')}")


def main() -> None:
    event = {
        "id": "evt_demo_0001",
        "type": "payment.succeeded",
        "data": {"payment_id": "pay_demo", "amount": 4999},
    }

    print("Sending a correctly signed webhook:")
    send_webhook(WEBHOOK_URL, event, WEBHOOK_SECRET)

    print("\nSending a payload that's tampered with after signing (should be rejected):")
    _demo_tampered_payload(WEBHOOK_URL, event, WEBHOOK_SECRET)


if __name__ == "__main__":
    main()
