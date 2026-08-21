"""Inbound webhook receiving: signature verification + deduplication."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.inbound_event import InboundEvent
from app.services.signing import verify


class InvalidSignatureError(Exception):
    pass


class InboundService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def verify_signature(self, *, payload_bytes: bytes, signature: str, timestamp: int) -> bool:
        return verify(
            payload_bytes,
            signature,
            settings.inbound_signing_secret,
            timestamp,
            tolerance_seconds=settings.replay_window_seconds,
        )

    async def get_by_dedupe_key(self, *, source: str, provider_event_id: str) -> InboundEvent | None:
        result = await self._session.execute(
            select(InboundEvent).where(
                InboundEvent.source == source, InboundEvent.provider_event_id == provider_event_id
            )
        )
        return result.scalar_one_or_none()

    async def record_event(
        self, *, source: str, provider_event_id: str, payload: dict, signature_valid: bool
    ) -> tuple[InboundEvent, bool]:
        """Returns (event, created). `created=False` means this was a
        duplicate delivery -- the (source, provider_event_id) unique
        constraint is the race-safe guard, not just an app-level check, per
        the production checklist."""
        existing = await self.get_by_dedupe_key(source=source, provider_event_id=provider_event_id)
        if existing is not None:
            return existing, False

        event = InboundEvent(
            source=source,
            provider_event_id=provider_event_id,
            payload=payload,
            signature_valid=signature_valid,
            processed_at=datetime.now(timezone.utc) if signature_valid else None,
        )
        self._session.add(event)
        try:
            await self._session.flush()
        except IntegrityError:
            # Concurrent duplicate delivery raced us to the unique
            # constraint -- fetch the winner and treat this as a dup too.
            await self._session.rollback()
            existing = await self.get_by_dedupe_key(source=source, provider_event_id=provider_event_id)
            assert existing is not None
            return existing, False
        return event, True
