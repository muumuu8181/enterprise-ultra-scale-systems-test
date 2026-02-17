import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.api.v1.emergency_vehicle import router as emergency_router

# テスト用アプリの構築
app = FastAPI()
app.include_router(emergency_router)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_register_vehicle(client):
    """
    緊急車両登録のテスト (DBなし)
    """
    payload = {
        "vehicle_id": "ambulance-001",
        "type": "ambulance"
    }
    response = await client.post("/emergency/vehicles/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == "ambulance-001"
    assert data["status"] == "registered (mock)"

@pytest.mark.asyncio
async def test_preemption_request(client):
    """
    優先制御要求のテスト (DBなし)
    """
    payload = {
        "vehicle_id": "ambulance-001",
        "route": {"intersection_ids": [1, 2, 3]},
        "eta": 300.0
    }

    response = await client.post("/emergency/preemption/request", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "accepted"

@pytest.mark.asyncio
async def test_preemption_status(client):
    """
    優先制御ステータス確認のテスト (DBなし)
    """
    request_id = "test-req-id"
    response = await client.get(f"/emergency/preemption/{request_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "granted (mock)"

@pytest.mark.asyncio
async def test_clearance_broadcast(client):
    """
    進路確保ブロードキャストのテスト
    """
    payload = {
        "location": {"lat": 35.6895, "lon": 139.6917},
        "radius": 1000.0,
        "message": "Warning!"
    }
    response = await client.post("/emergency/clearance/broadcast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "broadcast_sent"
    assert data["target_radius"] == 1000.0

@pytest.mark.asyncio
async def test_register_vehicle_invalid_type(client):
    """
    無効な車両タイプでの登録テスト
    """
    payload = {
        "vehicle_id": "ambulance-001",
        "type": "taxi" # invalid
    }
    response = await client.post("/emergency/vehicles/register", json=payload)
    assert response.status_code == 422 # Validation Error
