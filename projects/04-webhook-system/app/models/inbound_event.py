from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InboundEvent(Base):
    __tablename__ = "inbound_events"
    __table_args__ = (UniqueConstraint("source", "provider_event_id", name="uq_inbound_source_event"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
