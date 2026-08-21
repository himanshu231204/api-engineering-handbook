from __future__ import annotations

import os
from typing import AsyncIterator

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.routes import auth as auth_routes
from app.db.session import Base, get_session
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """The login/forgot-password rate limiters are process-local singletons
    (see app/services/rate_limiter.py); reset them before every test so
    one test's login attempts don't spuriously rate-limit another."""
    auth_routes._login_limiter.reset()
    auth_routes._forgot_limiter.reset()
    yield


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_local = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with test_session_local() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield test_session_local
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
