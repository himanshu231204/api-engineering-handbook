"""
SQLAlchemy engine/session setup.

Uses SQLite by default so the example runs with `pip install` + `uvicorn`
and nothing else -- no Postgres container required. Swap `DATABASE_URL` to
point this at Postgres and it works unchanged (see
docs/04-databases-and-apis/postgresql-integration and connection-pooling).
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False because FastAPI may serve a single
# connection's requests from different threads (Starlette's threadpool for
# sync endpoints). This is a SQLite-specific quirk, not general advice.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields one DB session per request and
    guarantees it's closed afterward, even if the handler raises."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
