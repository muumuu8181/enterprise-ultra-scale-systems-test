import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from src.main import app
from src.database import get_db
from src.models.transport_models import TransitVehicle, TransitStop, ArrivalPrediction
from datetime import datetime

# Test setup
@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.execute = AsyncMock()
    return session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _get_db():
        yield mock_db_session
    return _get_db

@pytest.fixture
async def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_bus_locations(client, mock_db_session):
    # Mock return data
    mock_vehicle = TransitVehicle(
        id=1,
        vehicle_id="bus-001",
        route_id="route-101",
        operator="CityBus",
        speed=30.0,
        heading=90.0,
        location="POINT(139.7 35.6)",
        updated_at="2023-01-01T00:00:00"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_vehicle]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/transport/buses/route-101/realtime")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["vehicle_id"] == "bus-001"

@pytest.mark.asyncio
async def test_get_stop_arrivals(client, mock_db_session):
    # Mock Stop
    mock_stop = TransitStop(stop_id="stop-A", name="Stop A")

    # Mock Prediction
    mock_prediction = ArrivalPrediction(
        stop_id="stop-A",
        vehicle_id="bus-001",
        predicted_arrival="2023-01-01T12:00:00",
        confidence=0.9
    )

    mock_result_stop = MagicMock()
    mock_result_stop.scalar_one_or_none.return_value = mock_stop

    mock_result_pred = MagicMock()
    mock_result_pred.scalars.return_value.all.return_value = [mock_prediction]

    # side_effect iterates over calls
    mock_db_session.execute.side_effect = [mock_result_stop, mock_result_pred]

    response = await client.get("/api/v1/transport/stops/stop-A/arrivals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["stop_id"] == "stop-A"

@pytest.mark.asyncio
async def test_update_vehicle_location(client, mock_db_session):
    mock_vehicle = TransitVehicle(
        id=1,
        vehicle_id="bus-001",
        route_id="route-1",
        operator="TestOp",
        updated_at=datetime.utcnow(),
        location="POINT(0 0)",
        speed=0,
        heading=0
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_vehicle
    mock_db_session.execute.return_value = mock_result

    payload = {
        "lat": 35.6895,
        "lon": 139.6917,
        "speed": 40.0,
        "heading": 180.0
    }

    response = await client.post("/api/v1/transport/vehicles/bus-001/location", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == "bus-001"
    assert data["speed"] == 40.0

    # Verify update on mock object
    assert mock_vehicle.speed == 40.0
    assert "POINT(139.6917 35.6895)" in str(mock_vehicle.location)

@pytest.mark.asyncio
async def test_optimize_route(client):
    response = await client.get("/api/v1/transport/route/optimize", params={
        "from": "35.0,139.0",
        "to": "35.1,139.1"
    })
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "segments" in data
