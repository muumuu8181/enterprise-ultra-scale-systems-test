import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.database import get_db
from unittest.mock import AsyncMock

# Mock DB dependency
async def override_get_db():
    mock_session = AsyncMock()
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Passenger Rail Platform API"}

@pytest.mark.asyncio
async def test_get_station_departures():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stations/1/departures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["train_id"] == "T101"

@pytest.mark.asyncio
async def test_report_disruption():
    payload = {
        "disruption_type": "signal",
        "affected_lines": ["L1"],
        "start_time": "2023-10-27T10:00:00Z",
        "passenger_impact": "High"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/disruptions/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reported"
    assert "replacement_plan" in data

@pytest.mark.asyncio
async def test_performance_kpis():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/operations/performance-kpis?line_id=L1")
    assert response.status_code == 200
    assert response.json()["punctuality_score"] == 98.5
