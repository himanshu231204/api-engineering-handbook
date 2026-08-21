"""Outbound dispatcher: fans an internal domain event out to one `deliveries`
row per matching, active subscription."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery, OutboundEvent
from app.models.subscription import Subscription
from app.core.config import settings


class Dispatcher:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def dispatch(self, *, event_type: str, payload: dict) -> OutboundEvent:
        event = OutboundEvent(event_type=event_type, payload=payload)
        self._session.add(event)
        await self._session.flush()

        result = await self._session.execute(
            select(Subscription).where(Subscription.status == "active")
        )
        subscriptions = [s for s in result.scalars().all() if event_type in s.event_types]

        for subscription in subscriptions:
            delivery = Delivery(
                subscription_id=subscription.id,
                event_id=event.id,
                status="pending",
                max_attempts=settings.max_delivery_attempts,
            )
            self._session.add(delivery)

        await self._session.flush()
        return event
