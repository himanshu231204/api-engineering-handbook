import pytest

CREDS = {"email": "login@example.com", "password": "GoodPass1"}


@pytest.mark.asyncio
async def test_login_success_issues_token_pair(client):
    await client.post("/auth/register", json=CREDS)
    resp = await client.post("/auth/login", json=CREDS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post("/auth/register", json=CREDS)
    resp = await client.post("/auth/login", json={**CREDS, "password": "WrongPass1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user_returns_401(client):
    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "GoodPass1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_rate_limited_after_threshold(client):
    await client.post("/auth/register", json=CREDS)
    bad = {**CREDS, "password": "WrongPass1"}
    last_status = None
    for _ in range(6):
        resp = await client.post("/auth/login", json=bad)
        last_status = resp.status_code
    assert last_status == 429


@pytest.mark.asyncio
async def test_me_requires_valid_access_token(client):
    await client.post("/auth/register", json=CREDS)
    tokens = (await client.post("/auth/login", json=CREDS)).json()
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == CREDS["email"]


@pytest.mark.asyncio
async def test_me_without_token_returns_401_or_403(client):
    resp = await client.get("/auth/me")
    assert resp.status_code in (401, 403)
