"""Shared HMAC-SHA256 sign/verify logic used by both the inbound receiver
(verifying a third party's signature) and the outbound dispatcher (signing
payloads sent to customers). See:
docs/09-realtime-and-webhooks/webhook-signature-verification.md
"""
from __future__ import annotations

import hashlib
import hmac
import time


def sign(payload_bytes: bytes, secret: str, *, timestamp: int | None = None) -> tuple[str, int]:
    """Returns (signature_hex, timestamp) for `t=<ts>.v1=<hmac>` style headers."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode("utf-8") + payload_bytes
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return signature, ts


def verify(
    payload_bytes: bytes,
    signature: str,
    secret: str,
    timestamp: int,
    *,
    tolerance_seconds: int = 300,
    now: int | None = None,
) -> bool:
    """Constant-time signature check plus a replay-protection timestamp
    freshness check. Returns False (never raises) on any mismatch."""
    current = now if now is not None else int(time.time())
    if abs(current - timestamp) > tolerance_seconds:
        return False

    expected_signature, _ = sign(payload_bytes, secret, timestamp=timestamp)
    return hmac.compare_digest(expected_signature, signature)
