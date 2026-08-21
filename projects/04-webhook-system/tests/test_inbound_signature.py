import json
import time

import pytest

from app.core.config import settings
from app.services.signing import sign

PAYLOAD = {"type": "payment.succeeded", "amount": 4200}


def _headers_for(payload: dict, *, secret: str = None, timestamp: int = None, event_id: str = "evt_1"):
    body = json.dumps(payload).encode("utf-8")
    secret = secret or settings.inbound_signing_secret
    signature, ts = sign(body, secret, timestamp=timestamp)
    return body, {
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(ts),
        "X-Event-Id": event_id,
        "Content-Type": "application/json",
    }


@pytest.mark.asyncio
async def test_valid_signature_accepted(client):
    body, headers = _headers_for(PAYLOAD)
    resp = await client.post("/webhooks/inbound/payments", content=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["duplicate"] is False


@pytest.mark.asyncio
async def test_invalid_signature_rejected(client):
    body, headers = _headers_for(PAYLOAD, secret="wrong-secret")
    resp = await client.post("/webhooks/inbound/payments", content=body, headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stale_timestamp_rejected_as_replay(client):
    old_timestamp = int(time.time()) - (settings.replay_window_seconds + 60)
    body, headers = _headers_for(PAYLOAD, timestamp=old_timestamp)
    resp = await client.post("/webhooks/inbound/payments", content=body, headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_signature_header_returns_422(client):
    body = json.dumps(PAYLOAD).encode("utf-8")
    resp = await client.post(
        "/webhooks/inbound/payments",
        content=body,
        headers={"X-Webhook-Timestamp": str(int(time.time())), "X-Event-Id": "evt_1"},
    )
    assert resp.status_code == 422
