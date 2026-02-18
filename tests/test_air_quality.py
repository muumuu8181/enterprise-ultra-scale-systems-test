import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.air_models import AQStation, AQReading, AQAlertRule
from src.services.aqi_calculator import AQICalculator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Test setup fixtures similar to existing tests
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
    # Using ASGITransport to test the app directly
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

# --- Unit Tests for Calculator ---

def test_aqi_calculator_pm25():
    # PM2.5 = 12.0 -> AQI 50
    aqi, poll = AQICalculator.calculate_aqi(pm25=12.0)
    assert aqi == 50
    assert poll == "pm25"

    # PM2.5 = 35.4 -> AQI 100
    aqi, poll = AQICalculator.calculate_aqi(pm25=35.4)
    assert aqi == 100

    # PM2.5 = 500.4 -> AQI 500
    aqi, poll = AQICalculator.calculate_aqi(pm25=500.4)
    assert aqi == 500

def test_aqi_calculator_multiple():
    # PM2.5=12.0 (AQI 50), PM10=155 (AQI 101) -> Max is PM10
    aqi, poll = AQICalculator.calculate_aqi(pm25=12.0, pm10=155.0)
    assert aqi == 101 # 155 is start of Unhealthy for Sensitive (101-150)
    # Calculation: (150-101)/(254-155) * (155-155) + 101 = 101
    assert poll == "pm10"

def test_aqi_level_string():
    assert AQICalculator.get_aqi_level(50) == "Good"
    assert AQICalculator.get_aqi_level(151) == "Unhealthy"
    assert AQICalculator.get_aqi_level(301) == "Hazardous"

def test_aqi_calculator_gap_values():
    # PM2.5 = 12.05 -> Truncate to 12.0 -> AQI 50
    aqi, poll = AQICalculator.calculate_aqi(pm25=12.05)
    assert aqi == 50

    # PM2.5 = 12.09 -> Truncate to 12.0 -> AQI 50
    aqi, poll = AQICalculator.calculate_aqi(pm25=12.09)
    assert aqi == 50

    # PM2.5 = 12.10 -> Truncate to 12.1 -> AQI 51
    aqi, poll = AQICalculator.calculate_aqi(pm25=12.10)
    assert aqi == 51

# --- Integration Tests for API ---

@pytest.mark.asyncio
async def test_get_stations(client, mock_db_session):
    # Mock DB result
    mock_station = AQStation(
        id=1,
        station_id="ST001",
        name="Tokyo Tower",
        operator="Gov",
        installed_at=datetime.utcnow(),
        location="POINT(139.7 35.6)" # Mocking the internal representation or just a string if simpler
    )

    # Since the endpoint uses to_shape(s.location), we need to mock to_shape or ensure s.location works.
    # It's easier to mock `to_shape` in the module.
    with patch("src.api.v1.air_quality.to_shape") as mock_to_shape:
        mock_shape = MagicMock()
        mock_shape.x = 139.7
        mock_shape.y = 35.6
        mock_to_shape.return_value = mock_shape

        # Setup mock execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_station]
        mock_db_session.execute.return_value = mock_result

        response = await client.get("/api/v1/air/stations")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["station_id"] == "ST001"
        assert data[0]["latitude"] == 35.6
        assert data[0]["longitude"] == 139.7

@pytest.mark.asyncio
async def test_get_station_current(client, mock_db_session):
    mock_reading = AQReading(
        id=10,
        station_id=1,
        timestamp=datetime.utcnow(),
        pm25=12.0,
        pm10=None,
        no2=None,
        o3=None,
        co=None,
        aqi=50 # Pre-calculated
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_reading
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/air/stations/1/current")

    assert response.status_code == 200
    data = response.json()
    assert data["pm25"] == 12.0
    assert data["aqi"] == 50
    assert data["aqi_level"] == "Good"

@pytest.mark.asyncio
async def test_get_station_current_calc_on_fly(client, mock_db_session):
    # AQI is None, should calculate
    mock_reading = AQReading(
        id=11,
        station_id=1,
        timestamp=datetime.utcnow(),
        pm25=35.4, # AQI 100
        pm10=None, no2=None, o3=None, co=None,
        aqi=None
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_reading
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/air/stations/1/current")

    assert response.status_code == 200
    data = response.json()
    assert data["aqi"] == 100
    assert data["aqi_level"] == "Moderate"

@pytest.mark.asyncio
async def test_get_forecast(client):
    response = await client.get("/api/v1/air/forecast?lat=35.0&lon=139.0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 24
    assert "time" in data[0]
    assert "aqi" in data[0]

@pytest.mark.asyncio
async def test_create_alert_rule(client, mock_db_session):
    payload = {
        "threshold_aqi": 150,
        "area_polygon": "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
    }

    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 1
        obj.created_at = datetime.utcnow()
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/air/alerts", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["threshold_aqi"] == 150
    assert mock_db_session.add.called
