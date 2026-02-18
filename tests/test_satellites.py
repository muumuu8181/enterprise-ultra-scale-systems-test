import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.space_models import Satellite, Telemetry, MissionCommand
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Test setup
@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
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
async def test_get_satellites(client, mock_db_session):
    mock_satellite = Satellite(id=1, name="Sat-1", orbit_type="LEO", inclination=45.0, altitude_km=500.0, status="active")

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_satellite]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/satellites/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Sat-1"

@pytest.mark.asyncio
async def test_get_telemetry(client, mock_db_session):
    mock_satellite = Satellite(id=1, name="Sat-1")
    mock_telemetry = Telemetry(
        id=1, satellite_id=1, timestamp=datetime.now(),
        position={"x": 0, "y": 0, "z": 0}, velocity={"vx": 0, "vy": 0, "vz": 0},
        battery_percent=90.0, temperature_c=25.0, anomalies={}
    )

    # First call: check satellite existence
    mock_result_sat = MagicMock()
    mock_result_sat.scalar_one_or_none.return_value = mock_satellite

    # Second call: get telemetry
    mock_result_tel = MagicMock()
    mock_result_tel.scalars.return_value.all.return_value = [mock_telemetry]

    mock_db_session.execute.side_effect = [mock_result_sat, mock_result_tel]

    response = await client.get("/api/v1/satellites/1/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["satellite_id"] == 1

@pytest.mark.asyncio
async def test_create_command(client, mock_db_session):
    mock_satellite = Satellite(id=1, name="Sat-1")

    # Check satellite existence
    mock_result_sat = MagicMock()
    mock_result_sat.scalar_one_or_none.return_value = mock_satellite
    mock_db_session.execute.return_value = mock_result_sat

    payload = {
        "command_type": "ORBIT_ADJUST",
        "parameters": {"delta_v": 10.0},
        "scheduled_at": datetime.now().isoformat()
    }

    async def mock_refresh(obj):
        obj.id = 100
        obj.satellite_id = 1
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/satellites/1/commands", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 100
    assert data["command_type"] == "ORBIT_ADJUST"
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_orbit_prediction(client, mock_db_session):
    mock_satellite = Satellite(id=1, name="Sat-1", altitude_km=500.0)

    # Check satellite existence
    mock_result_sat = MagicMock()
    mock_result_sat.scalar_one_or_none.return_value = mock_satellite
    mock_db_session.execute.return_value = mock_result_sat

    response = await client.get("/api/v1/satellites/1/orbit-prediction?hours=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["satellite_id"] == 1
