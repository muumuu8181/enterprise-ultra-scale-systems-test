import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.city_models import Sensor, SensorReading, Alert
from src.services.alert_engine import AlertEngine
from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_register_sensor_success(client, mock_db_session):
    payload = {
        "device_id": "sensor-001",
        "sensor_type": "temperature",
        "latitude": 35.6895,
        "longitude": 139.6917,
        "metadata_info": {"model": "T1000"}
    }
    # Mock refresh to set ID and default values
    async def mock_refresh(obj):
        obj.id = 1
        if not hasattr(obj, 'status') or obj.status is None:
            obj.status = "active"
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/sensors/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "sensor-001"
    assert data["id"] == 1
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_batch_readings_insertion(client, mock_db_session):
    sensor_id = 1
    payload = [
        {"value": 25.5, "unit": "celsius"},
        {"value": 26.0, "unit": "celsius"}
    ]

    # AlertEngine.evaluate_rules is called in the endpoint.
    # Since AlertEngine creates its own session, we might want to patch it or let it fail gracefully (caught in except?).
    # Or better, patch `src.api.v1.sensors.alert_engine.evaluate_rules`
    with patch("src.api.v1.sensors.alert_engine.evaluate_rules", new_callable=AsyncMock) as mock_evaluate:
        response = await client.post(f"/api/v1/sensors/{sensor_id}/readings", json=payload)
        assert response.status_code == 200
        assert "Inserted 2 readings" in response.json()["message"]
        assert mock_db_session.add_all.called
        assert mock_evaluate.call_count == 2

@pytest.mark.asyncio
async def test_nearby_sensors_query(client, mock_db_session):
    # Mock DB result
    mock_result = MagicMock()
    mock_sensor = Sensor(id=1, device_id="s1", sensor_type="temp", status="active", last_seen="2023-01-01T00:00:00")
    # Need to set attributes that might be accessed
    mock_result.scalars.return_value.all.return_value = [mock_sensor]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/sensors/nearby?lat=35.6895&lon=139.6917&radius=1000")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["device_id"] == "s1"

@pytest.mark.asyncio
async def test_alert_generation_on_threshold(mock_db_session):
    # Test AlertEngine directly
    # Patch AsyncSessionLocal used in AlertEngine
    with patch("src.services.alert_engine.AsyncSessionLocal") as mock_factory:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory.return_value.__aenter__.return_value = mock_session

        engine = AlertEngine()
        reading = SensorReading(sensor_id=1, value=0.95, unit="celsius") # Critical > 0.9

        await engine.evaluate_rules(reading)

        assert mock_session.add.called
        # Check if ANY call was with Alert (since EmergencyIncident is also added)
        alert_created = False
        for call in mock_session.add.call_args_list:
            args, _ = call
            if isinstance(args[0], Alert):
                alert = args[0]
                assert alert.severity == "CRITICAL"
                assert "critical value" in alert.message
                alert_created = True
                break
        assert alert_created
