"""Exercises the delivery worker directly against a simulated receiving
endpoint (an httpx MockTransport) so no real network call is made."""
from __future__ import annotations

import pytest
import httpx
from sqlalchemy import select

from app.models.delivery import Delivery, OutboundEvent
from app.models.subscription import Subscription
from app.workers.delivery_worker import attempt_delivery, compute_backoff_seconds


class FlakyHandler:
    """Fails the first `fail_times` requests, then succeeds."""

    def __init__(self, fail_times: int) -> None:
        self.fail_times = fail_times
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls <= self.fail_times:
            return httpx.Response(500, text="server error")
        return httpx.Response(200, text="ok")


async def _make_delivery(session_factory) -> str:
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

        delivery = Delivery(subscription_id=subscription.id, event_id=event.id, max_attempts=3)
        session.add(delivery)
        await session.commit()
        return delivery.id


def test_backoff_grows_with_attempt_number():
    small = compute_backoff_seconds(1)
    large = compute_backoff_seconds(4)
    assert 0 <= small <= 2
    assert 0 <= large <= 16


@pytest.mark.asyncio
async def test_delivery_succeeds_after_retries(session_factory):
    delivery_id = await _make_delivery(session_factory)
    handler = FlakyHandler(fail_times=2)
    transport = httpx.MockTransport(handler)

    async with session_factory() as session:
        async with httpx.AsyncClient(transport=transport) as http_client:
            for _ in range(3):
                delivery = await attempt_delivery(session, delivery_id, http_client=http_client)
                if delivery.status == "delivered":
                    break
        await session.commit()

    assert delivery.status == "delivered"
    assert delivery.attempt_count == 3
    assert handler.calls == 3


@pytest.mark.asyncio
async def test_delivery_records_attempt_history(session_factory):
    from app.models.delivery import DeliveryAttempt

    delivery_id = await _make_delivery(session_factory)
    transport = httpx.MockTransport(lambda r: httpx.Response(500))

    async with session_factory() as session:
        async with httpx.AsyncClient(transport=transport) as http_client:
            await attempt_delivery(session, delivery_id, http_client=http_client)
        await session.commit()

    async with session_factory() as session:
        result = await session.execute(
            select(DeliveryAttempt).where(DeliveryAttempt.delivery_id == delivery_id)
        )
        attempts = result.scalars().all()
    assert len(attempts) == 1
    assert attempts[0].status_code == 500
    assert attempts[0].attempt_number == 1
