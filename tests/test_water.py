import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.water_models import WaterPressureSensor, WaterLeak, WaterQualityReading
from unittest.mock import AsyncMock, MagicMock
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
async def test_get_pressure(client, mock_db_session):
    # Mock DB result
    mock_result = MagicMock()
    mock_sensor = WaterPressureSensor(
        id=1,
        zone_id="zone-A",
        pressure_bar=3.5,
        timestamp=datetime.utcnow()
    )
    mock_result.scalars.return_value.all.return_value = [mock_sensor]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/water/pressure/zone-A")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["zone_id"] == "zone-A"
    assert data[0]["pressure_bar"] == 3.5

@pytest.mark.asyncio
async def test_report_leak(client, mock_db_session):
    payload = {
        "latitude": 35.6895,
        "longitude": 139.6917,
        "severity": "High",
        "estimated_loss_liters": 1000.0
    }

    async def mock_refresh(obj):
        obj.id = 1
        obj.reported_at = datetime.utcnow()
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/water/leaks/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "High"
    assert data["id"] == 1
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_active_leaks(client, mock_db_session):
    mock_result = MagicMock()
    mock_leak = WaterLeak(
        id=1,
        severity="Medium",
        reported_at=datetime.utcnow(),
        repaired_at=None,
        estimated_loss_liters=500.0
    )
    mock_result.scalars.return_value.all.return_value = [mock_leak]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/water/leaks/active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["severity"] == "Medium"

@pytest.mark.asyncio
async def test_get_quality(client, mock_db_session):
    mock_result = MagicMock()
    mock_quality = WaterQualityReading(
        id=1,
        station_id="ST-01",
        ph=7.2,
        turbidity=0.5,
        chlorine_residual=0.3,
        timestamp=datetime.utcnow()
    )
    mock_result.scalars.return_value.all.return_value = [mock_quality]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/water/quality/ST-01")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["station_id"] == "ST-01"
    assert data[0]["ph"] == 7.2

@pytest.mark.asyncio
async def test_control_valve(client):
    payload = {"action": "open"}
    response = await client.post("/api/v1/water/valve/V-100/control", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["action"] == "open"
    assert "V-100" in data["message"]

@pytest.mark.asyncio
async def test_control_valve_invalid(client):
    payload = {"action": "break"}
    response = await client.post("/api/v1/water/valve/V-100/control", json=payload)
    assert response.status_code == 400
