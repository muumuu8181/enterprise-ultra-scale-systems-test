import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.energy_models import SmartMeter, EnergyReading, DemandResponse
from unittest.mock import AsyncMock, MagicMock, patch
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
async def test_get_district_consumption(client, mock_db_session):
    # Mock result for sum query
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1234.56
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/energy/consumption?district=Shibuya")
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Shibuya"
    assert data["total_consumption_kwh"] == 1234.56

@pytest.mark.asyncio
async def test_add_meter_reading(client, mock_db_session):
    # Mock SmartMeter lookup
    mock_meter = SmartMeter(id=10, meter_id="SM-001", district="Shibuya")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_meter
    mock_db_session.execute.return_value = mock_result

    # Mock refresh to populate reading ID
    async def mock_refresh(obj):
        obj.id = 100
        obj.meter_id = 10
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "kwh": 50.5,
        "voltage": 200.0,
        "current": 10.0,
        "power_factor": 0.95
    }

    response = await client.post("/api/v1/energy/meters/SM-001/reading", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 100
    assert data["meter_id"] == 10
    assert data["kwh"] == 50.5

    # Verify add was called
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_forecast(client, mock_db_session):
    # Mock DB query for history
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/energy/forecast?hours=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    assert "timestamp" in data[0]
    assert "predicted_kwh" in data[0]

@pytest.mark.asyncio
async def test_create_demand_response(client, mock_db_session):
    async def mock_refresh(obj):
        obj.id = 5
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "reduction_target_kw": 500.0,
        "duration_minutes": 60
    }

    response = await client.post("/api/v1/energy/demand-response", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["target_reduction"] == 500.0
    assert data["id"] == 5
    assert mock_db_session.add.called
