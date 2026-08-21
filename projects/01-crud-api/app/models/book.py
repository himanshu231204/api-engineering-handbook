"""SQLAlchemy ORM model for a book."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("isbn", name="uq_books_isbn"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(300), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    published_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)
