import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from geoalchemy2.elements import WKTElement

from src.api.v1.pedestrian import router as pedestrian_router, get_db
from src.models.pedestrian_models import PedestrianDevice
from src.models.v2x_models import Vehicle

# Create Test App
app = FastAPI()
app.include_router(pedestrian_router)

# Mock DB Session
class MockResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return self

    def all(self):
        return self._data

    def scalar_one_or_none(self):
        if self._data and len(self._data) > 0:
            return self._data[0]
        return None

mock_session = AsyncMock()
mock_session.add = MagicMock()

async def override_get_db():
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    # Reset mock after test
    mock_session.reset_mock()

@pytest.mark.asyncio
async def test_register_device(client):
    # Mocking duplicate check: returns None (no existing device)
    mock_session.execute.return_value = MockResult([])

    payload = {"device_id": "ped-001", "device_type": "smartphone"}
    response = await client.post("/pedestrian/devices/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "registered"
    assert data["device_id"] == "ped-001"

    # Verify DB add was called
    assert mock_session.add.called

@pytest.mark.asyncio
async def test_update_location_with_conflict(client):
    # 1. Mock db.get(PedestrianDevice)
    ped_device = PedestrianDevice(id=1, device_id="ped-001", location="POINT(0 0)")
    mock_session.get.return_value = ped_device

    # 2. Mock db.execute(Vehicle query)
    # Scenario: Vehicle 11m North (lat 0.0001 approx), heading South (180), speed 10m/s.
    # Pedestrian at 0,0, speed 0.
    # Distance ~11.1m. Closing speed ~10m/s. TTC ~1.1s < 3s.

    vehicle = Vehicle(vehicle_id="veh-001", speed=10.0, heading=180.0)
    # The query returns rows of (Vehicle, lon, lat)
    # lat 0.0001 is approx 11.1 meters North of 0.0
    rows = [(vehicle, 0.0, 0.0001)]

    mock_session.execute.return_value = MockResult(rows)

    payload = {
        "lat": 0.0,
        "lon": 0.0,
        "speed": 0.0,
        "heading": 0.0
    }

    response = await client.post("/pedestrian/devices/1/location", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert len(data["alerts"]) > 0

    alert = data["alerts"][0]
    assert alert["vehicle_id"] == "veh-001"
    assert alert["ttc"] < 3.0

    # Verify alert added to DB
    assert mock_session.add.call_count >= 1 # Could be 0 if commit logic handled differently, but logic calls add inside loop

@pytest.mark.asyncio
async def test_get_nearby_alerts(client):
    # Mock db.execute(SafetyAlert query)
    # Return some mock alerts
    # Since the query returns scalars().all(), we simulate that structure.

    # Wait, MockResult.scalars().all() returns self._data.
    # So we pass a list of SafetyAlert objects.

    alert1 = MagicMock() # Use MagicMock for simple object
    alert1.id = 1
    alert1.vehicle_id = "v1"
    alert1.pedestrian_id = "p1"
    alert1.ttc_seconds = 1.5
    alert1.distance_m = 10.0
    alert1.created_at = datetime.now(timezone.utc)

    mock_session.execute.return_value = MockResult([alert1])

    response = await client.get("/pedestrian/alerts?lat=0&lon=0")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["vehicle_id"] == "v1"
