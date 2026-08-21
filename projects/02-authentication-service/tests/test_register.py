import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "password": "GoodPass1"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "a@example.com"
    assert body["role"] == "user"
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dup@example.com", "password": "GoodPass1"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client):
    resp = await client.post("/auth/register", json={"email": "weak@example.com", "password": "short"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_rejected(client):
    resp = await client.post("/auth/register", json={"email": "not-an-email", "password": "GoodPass1"})
    assert resp.status_code == 422
