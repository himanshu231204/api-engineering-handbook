"""The delivery worker: attempts a single due delivery, signs the payload,
POSTs it, records the attempt, and applies exponential-backoff-with-jitter
retry scheduling or dead-letters the delivery once attempts are exhausted.

This reference implementation exposes the worker as a plain async function
you call per-delivery (`attempt_delivery`) rather than a standing polling
loop, so it is easy to unit test and easy to wire into a real scheduler
(a cron job, an RQ/Celery task, or a simple `while True` poll loop in
production -- see Part 8 for message-queue alternatives to polling).
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.delivery import Delivery, DeliveryAttempt, OutboundEvent
from app.models.subscription import Subscription
from app.services.signing import sign


def compute_backoff_seconds(attempt_number: int) -> float:
    """Exponential backoff with full jitter: base * 2^(n-1), randomized."""
    base = settings.base_backoff_seconds * (2 ** (attempt_number - 1))
    return random.uniform(0, base)


async def _get_delivery_context(
    session: AsyncSession, delivery_id: str
) -> Optional[tuple[Delivery, Subscription, OutboundEvent]]:
    delivery = await session.get(Delivery, delivery_id)
    if delivery is None:
        return None
    subscription = await session.get(Subscription, delivery.subscription_id)
    event = await session.get(OutboundEvent, delivery.event_id)
    if subscription is None or event is None:
        return None
    return delivery, subscription, event


async def attempt_delivery(
    session: AsyncSession, delivery_id: str, *, http_client: Optional[httpx.AsyncClient] = None
) -> Delivery:
    """Makes exactly one delivery attempt for `delivery_id` and updates its
    state accordingly. Caller is responsible for calling this again for a
    `retrying` delivery once `next_attempt_at` has passed."""
    ctx = await _get_delivery_context(session, delivery_id)
    if ctx is None:
        raise ValueError(f"delivery {delivery_id} (or its subscription/event) not found")
    delivery, subscription, event = ctx

    body = json.dumps(event.payload, sort_keys=True).encode("utf-8")
    signature, timestamp = sign(body, subscription.signing_secret)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(timestamp),
        "X-Webhook-Event-Type": event.event_type,
    }

    attempt_number = delivery.attempt_count + 1
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_snippet: Optional[str] = None

    owns_client = http_client is None
    client = http_client or httpx.AsyncClient(timeout=settings.delivery_timeout_seconds)
    try:
        try:
            response = await client.post(subscription.target_url, content=body, headers=headers)
            status_code = response.status_code
            response_snippet = response.text[:2000]
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as exc:
            error = f"{type(exc).__name__}: {exc}"
    finally:
        if owns_client:
            await client.aclose()

    delivery.attempt_count = attempt_number
    delivery.last_status_code = status_code
    delivery.last_error = error

    session.add(
        DeliveryAttempt(
            delivery_id=delivery.id,
            attempt_number=attempt_number,
            status_code=status_code,
            response_snippet=response_snippet,
            error=error,
        )
    )

    succeeded = status_code is not None and 200 <= status_code < 300
    if succeeded:
        delivery.status = "delivered"
        delivery.next_attempt_at = None
    elif attempt_number >= delivery.max_attempts:
        delivery.status = "dead_letter"
        delivery.next_attempt_at = None
    else:
        delivery.status = "retrying"
        backoff = compute_backoff_seconds(attempt_number)
        delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)

    await session.flush()
    return delivery


async def due_delivery_ids(session: AsyncSession, *, limit: int = 50) -> list[str]:
    """Deliveries that are pending, or retrying and past their backoff."""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Delivery.id)
        .where(
            Delivery.status.in_(["pending", "retrying"]),
            (Delivery.next_attempt_at.is_(None)) | (Delivery.next_attempt_at <= now),
        )
        .limit(limit)
    )
    return [row[0] for row in result.all()]
