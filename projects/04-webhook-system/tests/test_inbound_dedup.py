import json

import pytest

from app.services.signing import sign
from app.core.config import settings

PAYLOAD = {"type": "payment.succeeded", "amount": 4200}


def _headers(event_id: str):
    body = json.dumps(PAYLOAD).encode("utf-8")
    signature, ts = sign(body, settings.inbound_signing_secret)
    return body, {
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(ts),
        "X-Event-Id": event_id,
        "Content-Type": "application/json",
    }


@pytest.mark.asyncio
async def test_duplicate_delivery_is_deduped(client):
    body, headers = _headers("evt_dup")
    first = await client.post("/webhooks/inbound/payments", content=body, headers=headers)
    second = await client.post("/webhooks/inbound/payments", content=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert first.json()["event_id"] == second.json()["event_id"]


@pytest.mark.asyncio
async def test_different_event_ids_are_not_deduped(client):
    body1, headers1 = _headers("evt_a")
    body2, headers2 = _headers("evt_b")
    resp1 = await client.post("/webhooks/inbound/payments", content=body1, headers=headers1)
    resp2 = await client.post("/webhooks/inbound/payments", content=body2, headers=headers2)
    assert resp1.json()["event_id"] != resp2.json()["event_id"]


@pytest.mark.asyncio
async def test_same_event_id_different_source_not_deduped(client):
    body, headers_a = _headers("evt_shared")
    _, headers_b = _headers("evt_shared")
    resp1 = await client.post("/webhooks/inbound/source-a", content=body, headers=headers_a)
    resp2 = await client.post("/webhooks/inbound/source-b", content=body, headers=headers_b)
    assert resp1.json()["duplicate"] is False
    assert resp2.json()["duplicate"] is False


@pytest.mark.asyncio
async def test_list_inbound_events(client):
    body, headers = _headers("evt_list")
    await client.post("/webhooks/inbound/payments", content=body, headers=headers)
    resp = await client.get("/webhooks/inbound/events")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
