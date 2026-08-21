import pytest

CREDS = {"email": "refresh@example.com", "password": "GoodPass1"}


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_old_one_stops_working(client):
    await client.post("/auth/register", json=CREDS)
    tokens = (await client.post("/auth/login", json=CREDS)).json()
    old_refresh = tokens["refresh_token"]

    first_refresh = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert first_refresh.status_code == 200
    new_tokens = first_refresh.json()
    assert new_tokens["refresh_token"] != old_refresh

    # Reusing the now-revoked old refresh token must fail (reuse detection).
    reuse_attempt = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_attempt.status_code == 401


@pytest.mark.asyncio
async def test_reuse_detection_revokes_the_new_token_too(client):
    await client.post("/auth/register", json=CREDS)
    tokens = (await client.post("/auth/login", json=CREDS)).json()
    old_refresh = tokens["refresh_token"]

    first = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    new_refresh = first.json()["refresh_token"]

    # Trigger reuse detection on the old token.
    await client.post("/auth/refresh", json={"refresh_token": old_refresh})

    # The token issued by the legitimate rotation should now also be dead,
    # since reuse detection revokes the whole family.
    resp = await client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_unknown_token_returns_401(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_then_refresh_fails(client):
    await client.post("/auth/register", json=CREDS)
    tokens = (await client.post("/auth/login", json=CREDS)).json()

    logout_resp = await client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_resp.status_code == 204

    refresh_resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_resp.status_code == 401
