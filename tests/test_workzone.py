import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta

from src.api.v1.work_zone import router as workzone_router

# Test app
app = FastAPI()
app.include_router(workzone_router)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_work_zone(client):
    payload = {
        "location": "POLYGON((139.69 35.69, 139.70 35.69, 139.70 35.70, 139.69 35.70, 139.69 35.69))",
        "contractor": "Test Construction Co.",
        "speed_limit": 40.0,
        "lane_closures": {"1": "closed"},
        "start_date": str(datetime.now(timezone.utc)),
        "end_date": str(datetime.now(timezone.utc) + timedelta(days=1))
    }
    response = await client.post("/workzone/zones", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["mock"] is True

@pytest.mark.asyncio
async def test_get_active_zones(client):
    response = await client.get("/workzone/zones/active")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_update_status(client):
    response = await client.put("/workzone/zones/1/status", json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["new_status"] == "completed"

@pytest.mark.asyncio
async def test_broadcast(client):
    response = await client.post("/workzone/zones/1/broadcast")
    assert response.status_code == 200
    assert response.json()["status"] == "broadcasted"
