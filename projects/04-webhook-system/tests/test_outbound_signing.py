import json
import time

import pytest

from app.services.signing import sign, verify


def test_sign_then_verify_round_trips():
    payload = json.dumps({"hello": "world"}, sort_keys=True).encode("utf-8")
    signature, ts = sign(payload, "my-secret")
    assert verify(payload, signature, "my-secret", ts) is True


def test_verify_fails_with_wrong_secret():
    payload = b'{"hello":"world"}'
    signature, ts = sign(payload, "my-secret")
    assert verify(payload, signature, "different-secret", ts) is False


def test_verify_fails_with_tampered_payload():
    payload = b'{"amount":100}'
    signature, ts = sign(payload, "my-secret")
    tampered = b'{"amount":100000}'
    assert verify(tampered, signature, "my-secret", ts) is False


def test_verify_fails_outside_tolerance_window():
    payload = b'{"hello":"world"}'
    old_ts = int(time.time()) - 3600
    signature, _ = sign(payload, "my-secret", timestamp=old_ts)
    assert verify(payload, signature, "my-secret", old_ts, tolerance_seconds=300) is False


@pytest.mark.asyncio
async def test_subscription_creation_returns_secret_once(client):
    resp = await client.post(
        "/subscriptions",
        json={"customer_id": "cust_1", "target_url": "https://example.com/hooks", "event_types": ["order.created"]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "signing_secret" in body
    assert len(body["signing_secret"]) > 0

    listing = await client.get("/subscriptions", params={"customer_id": "cust_1"})
    assert listing.status_code == 200
    assert "signing_secret" not in listing.json()[0]


@pytest.mark.asyncio
async def test_ssrf_blocked_target_url_rejected(client):
    resp = await client.post(
        "/subscriptions",
        json={"customer_id": "cust_1", "target_url": "http://127.0.0.1:8000/hook", "event_types": ["x"]},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rotate_secret_keeps_previous_during_grace_period(client):
    created = (
        await client.post(
            "/subscriptions",
            json={"customer_id": "cust_2", "target_url": "https://example.com/hooks", "event_types": ["x"]},
        )
    ).json()
    resp = await client.post(f"/subscriptions/{created['id']}/rotate-secret")
    assert resp.status_code == 200
    body = resp.json()
    assert body["signing_secret"] != created["signing_secret"]
    assert "previous_secret_valid_until" in body
