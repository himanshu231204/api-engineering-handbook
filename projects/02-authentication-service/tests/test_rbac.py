import pytest
from sqlalchemy import select

from app.models.user import User

ADMIN_CREDS = {"email": "admin@example.com", "password": "GoodPass1"}
USER_CREDS = {"email": "user@example.com", "password": "GoodPass1"}


async def _promote_to_admin(session_factory, email: str) -> None:
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = "admin"
        await session.commit()


@pytest.mark.asyncio
async def test_regular_user_forbidden_from_admin_route(client):
    await client.post("/auth/register", json=USER_CREDS)
    tokens = (await client.post("/auth/login", json=USER_CREDS)).json()
    resp = await client.get("/admin/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_users(client, session_factory):
    await client.post("/auth/register", json=ADMIN_CREDS)
    await _promote_to_admin(session_factory, ADMIN_CREDS["email"])

    tokens = (await client.post("/auth/login", json=ADMIN_CREDS)).json()
    resp = await client.get("/admin/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert ADMIN_CREDS["email"] in emails


@pytest.mark.asyncio
async def test_admin_route_requires_auth(client):
    resp = await client.get("/admin/users")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_password_reset_flow_and_session_invalidation(client):
    await client.post("/auth/register", json=USER_CREDS)
    tokens = (await client.post("/auth/login", json=USER_CREDS)).json()

    forgot = await client.post("/auth/password/forgot", json={"email": USER_CREDS["email"]})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert reset_token

    reset_resp = await client.post(
        "/auth/password/reset", json={"reset_token": reset_token, "new_password": "NewGoodPass1"}
    )
    assert reset_resp.status_code == 204

    # Old refresh token must be dead after a password reset.
    refresh_resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_resp.status_code == 401

    # Old password no longer works; new one does.
    old_login = await client.post("/auth/login", json=USER_CREDS)
    assert old_login.status_code == 401
    new_login = await client.post(
        "/auth/login", json={"email": USER_CREDS["email"], "password": "NewGoodPass1"}
    )
    assert new_login.status_code == 200
