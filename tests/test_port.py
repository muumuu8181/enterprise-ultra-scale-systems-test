import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_get_vessel_schedule():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/ports/1/vessel-schedule")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_register_port_call():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/port-calls/register", json={
            "vessel_id": "V-001",
            "port_id": "P-001",
            "eta": "2023-10-27T10:00:00Z"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["vessel_id"] == "V-001"
    assert data["status"] == "registered"
