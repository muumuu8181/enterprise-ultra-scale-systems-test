import pytest
from httpx import AsyncClient
from src.core.security import create_access_token, create_refresh_token
from datetime import timedelta

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_customer):
    response = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "1234"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_pin(client: AsyncClient, test_customer):
    response = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "0000"})
    assert response.status_code == 401
    assert response.json()["detail"] == "顧客IDまたはPINが間違っています。"

@pytest.mark.asyncio
async def test_login_invalid_user(client: AsyncClient, test_customer):
    response = await client.post("/api/v1/auth/login", json={"customer_id": "nonexistent", "pin": "1234"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_protected_route(client: AsyncClient, test_customer):
    # Login to get token
    login_res = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "1234"})
    token = login_res.json()["access_token"]

    # Use token (Logout is a protected route)
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "ログアウトしました。"

@pytest.mark.asyncio
async def test_access_without_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/logout")
    # Middleware should return 401
    assert response.status_code == 401
    assert "認証情報が不足" in response.json()["detail"]

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, test_customer):
    # Login
    login_res = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "1234"})
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_access = refresh_res.json()["access_token"]
    new_refresh = refresh_res.json()["refresh_token"]

    assert new_access != login_res.json()["access_token"]
    assert new_refresh != refresh_token

    # Old refresh token should be blacklisted (or invalid)
    # Trying to reuse old refresh token
    reuse_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_res.status_code == 401
    assert "使用済みか無効" in reuse_res.json()["detail"]

@pytest.mark.asyncio
async def test_logout_blacklists_token(client: AsyncClient, test_customer):
    # Login
    login_res = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "1234"})
    token = login_res.json()["access_token"]

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_res.status_code == 200

    # Try to use token again (e.g. for logout again or another protected route)
    # Since we don't have another protected route easily, we use logout again
    retry_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert retry_res.status_code == 401
    assert "トークンが無効化" in retry_res.json()["detail"]

@pytest.mark.asyncio
async def test_rate_limit(client: AsyncClient, test_customer):
    # Simulate hitting rate limit
    # Limit is 5 per 60s

    # Patch rate limiter or just loop
    # Since we are using FakeRedis, the rate limiter logic in security.py should work.

    # Successful logins
    for _ in range(5):
        res = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "1234"})
        if res.status_code != 200:
            # If we hit it early, that's fine too, but we expect 5 to pass
            pass

    # 6th request
    res = await client.post("/api/v1/auth/login", json={"customer_id": "user1", "pin": "1234"})
    assert res.status_code == 429
    assert "試行回数が制限を超えました" in res.json()["detail"]
