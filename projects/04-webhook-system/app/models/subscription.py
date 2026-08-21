from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    event_types: Mapped[list] = mapped_column(JSON, nullable=False)
    signing_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    previous_secret: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, default=None)
    secret_rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
