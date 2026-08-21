"""Processing for accepted inbound events.

In this reference implementation, valid inbound events are marked
processed synchronously at receipt time (see
app/services/inbound_service.py) since there is no real downstream side
effect to perform -- the point of the project is proving signature
verification and deduplication work. A production system would instead
enqueue the event here and let a worker like this one process it
asynchronously (see Part 8 -- Async Systems) so the inbound HTTP response
returns immediately.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbound_event import InboundEvent


async def process_inbound_event(session: AsyncSession, event: InboundEvent) -> InboundEvent:
    if event.processed_at is None and event.signature_valid:
        event.processed_at = datetime.now(timezone.utc)
        await session.flush()
    return event
