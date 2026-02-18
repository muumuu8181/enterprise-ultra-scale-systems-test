import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_flow(client: AsyncClient):
    # Register
    res = await client.post("/auth/register", json={
        "username": "tester",
        "email": "tester@example.com",
        "password": "secret_password"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Login
    res = await client.post("/auth/login", json={
        "email": "tester@example.com",
        "password": "secret_password"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Login Failure
    res = await client.post("/auth/login", json={
        "email": "tester@example.com",
        "password": "wrong_password"
    })
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_guest_flow(client: AsyncClient):
    # Guest
    res = await client.post("/auth/guest", json={
        "device_id": "device_xyz",
        "platform": "ios"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Link Account
    res = await client.post("/auth/link-account",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "linked@example.com",
            "password": "new_password"
        }
    )
    assert res.status_code == 200

    # Verify linked account works
    res = await client.post("/auth/login", json={
        "email": "linked@example.com",
        "password": "new_password"
    })
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_duplicate_email(client: AsyncClient):
    # Register 1
    await client.post("/auth/register", json={
        "username": "u1",
        "email": "dup@example.com",
        "password": "p1"
    })

    # Register 2 (Fail)
    res = await client.post("/auth/register", json={
        "username": "u2",
        "email": "dup@example.com",
        "password": "p2"
    })
    assert res.status_code == 400
    assert "Email already registered" in res.json()["detail"]
