import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.city_models import Sensor
from src.models.noise_models import NoiseReading, NoiseComplaint
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.get = AsyncMock()
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
async def test_get_noise_sensors(client, mock_db_session):
    from datetime import datetime
    mock_sensor = Sensor(id=1, device_id="n1", sensor_type="noise", status="active", last_seen=datetime.utcnow())
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_sensor]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/noise/sensors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sensor_type"] == "noise"

@pytest.mark.asyncio
async def test_add_noise_reading(client, mock_db_session):
    # Mock finding sensor
    mock_sensor = Sensor(id=1, sensor_type="noise")
    mock_db_session.get.return_value = mock_sensor

    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 100
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {"db_level": 75.5, "frequency_hz": 1000}
    response = await client.post("/api/v1/noise/sensors/1/reading", json=payload)

    assert response.status_code == 200
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_add_noise_reading_invalid_sensor(client, mock_db_session):
    # Mock sensor not found
    mock_db_session.get.return_value = None

    payload = {"db_level": 75.5, "frequency_hz": 1000}
    response = await client.post("/api/v1/noise/sensors/999/reading", json=payload)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_heatmap(client, mock_db_session):
    # Mock DB response for the complex join query
    mock_result = MagicMock()
    # Row needs access by attribute for .db_level and .geojson
    mock_row = MagicMock()
    mock_row.db_level = 80.0
    mock_row.geojson = '{"type": "Point", "coordinates": [139.6917, 35.6895]}'

    mock_result.all.return_value = [mock_row]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/noise/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["db_level"] == 80.0

@pytest.mark.asyncio
async def test_report_complaint(client, mock_db_session):
    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 200
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "latitude": 35.6,
        "longitude": 139.7,
        "db_level": 90,
        "description": "Too loud!"
    }
    response = await client.post("/api/v1/noise/complaints", json=payload)
    assert response.status_code == 200
    assert mock_db_session.add.called
