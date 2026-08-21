from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OutboundEvent(Base):
    __tablename__ = "outbound_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_type: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    subscription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("outbound_events.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=_now)
    last_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    last_error: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    delivery_id: Mapped[str] = mapped_column(String(36), ForeignKey("deliveries.id", ondelete="CASCADE"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    response_snippet: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True, default=None)
    error: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default=None)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
