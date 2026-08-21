from __future__ import annotations

import httpx
import pytest

from app.models.delivery import Delivery, OutboundEvent
from app.models.subscription import Subscription
from app.workers.delivery_worker import attempt_delivery


async def _make_delivery(session_factory, *, max_attempts: int = 2) -> str:
    async with session_factory() as session:
        subscription = Subscription(
            customer_id="cust_1",
            target_url="https://example.com/hooks",
            event_types=["order.created"],
            signing_secret="s3cret",
            status="active",
        )
        session.add(subscription)
        await session.flush()

        event = OutboundEvent(event_type="order.created", payload={"order_id": 1})
        session.add(event)
        await session.flush()

        delivery = Delivery(subscription_id=subscription.id, event_id=event.id, max_attempts=max_attempts)
        session.add(delivery)
        await session.commit()
        return delivery.id


@pytest.mark.asyncio
async def test_delivery_dead_letters_after_max_attempts(session_factory):
    delivery_id = await _make_delivery(session_factory, max_attempts=2)
    transport = httpx.MockTransport(lambda r: httpx.Response(500, text="nope"))

    async with session_factory() as session:
        async with httpx.AsyncClient(transport=transport) as http_client:
            for _ in range(2):
                delivery = await attempt_delivery(session, delivery_id, http_client=http_client)
        await session.commit()

    assert delivery.status == "dead_letter"
    assert delivery.attempt_count == 2
    assert delivery.next_attempt_at is None


@pytest.mark.asyncio
async def test_redeliver_resets_dead_lettered_delivery(client, session_factory):
    delivery_id = await _make_delivery(session_factory, max_attempts=1)
    transport = httpx.MockTransport(lambda r: httpx.Response(500))

    async with session_factory() as session:
        async with httpx.AsyncClient(transport=transport) as http_client:
            await attempt_delivery(session, delivery_id, http_client=http_client)
        await session.commit()

    resp = await client.post(f"/deliveries/{delivery_id}/redeliver")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["attempt_count"] == 0


@pytest.mark.asyncio
async def test_dead_letters_listed_via_api(client, session_factory):
    delivery_id = await _make_delivery(session_factory, max_attempts=1)
    transport = httpx.MockTransport(lambda r: httpx.Response(500))

    async with session_factory() as session:
        async with httpx.AsyncClient(transport=transport) as http_client:
            await attempt_delivery(session, delivery_id, http_client=http_client)
        await session.commit()

    resp = await client.get("/dead-letters")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["items"]]
    assert delivery_id in ids


@pytest.mark.asyncio
async def test_get_delivery_detail_includes_attempts(client, session_factory):
    delivery_id = await _make_delivery(session_factory, max_attempts=3)
    transport = httpx.MockTransport(lambda r: httpx.Response(200))

    async with session_factory() as session:
        async with httpx.AsyncClient(transport=transport) as http_client:
            await attempt_delivery(session, delivery_id, http_client=http_client)
        await session.commit()

    resp = await client.get(f"/deliveries/{delivery_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "delivered"
    assert len(body["attempts"]) == 1


@pytest.mark.asyncio
async def test_get_missing_delivery_returns_404(client):
    resp = await client.get("/deliveries/does-not-exist")
    assert resp.status_code == 404
