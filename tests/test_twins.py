import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from unittest.mock import AsyncMock, MagicMock, patch
from src.models.twin_models import DigitalTwin, TwinState, TwinSimulation
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
async def test_register_twin(client, mock_db_session):
    payload = {
        "physical_asset_id": "building-101",
        "asset_type": "building",
        "model_uri": "s3://models/building-101.glb",
        "sync_interval_sec": 120
    }

    async def mock_refresh(obj):
        obj.id = 1
        obj.last_sync = None
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/twins/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["physical_asset_id"] == "building-101"
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_sync_twin(client, mock_db_session):
    twin_id = 1
    payload = {"state_data": {"temperature": 25.0, "occupancy": 10}}

    # Mock existing twin
    mock_twin = DigitalTwin(id=twin_id, physical_asset_id="b1", asset_type="building")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_twin
    mock_db_session.execute.return_value = mock_result

    async def mock_refresh(obj):
        obj.id = 100 # state id
        obj.timestamp = datetime.utcnow() # Ensure timestamp is set
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post(f"/api/v1/twins/{twin_id}/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["twin_id"] == twin_id
    assert data["state_data"]["temperature"] == 25.0
    assert mock_db_session.add.call_count >= 2 # twin and state

@pytest.mark.asyncio
async def test_simulate_twin(client, mock_db_session):
    twin_id = 1
    payload = {
        "scenario_name": "fire_drill",
        "parameters": {"intensity": "high"}
    }

    # Mock twin exists
    mock_twin = DigitalTwin(id=twin_id)
    # Mock simulation creation
    mock_sim = TwinSimulation(id=5, twin_id=twin_id, status="queued")

    # Mock get_twin return
    mock_result_twin = MagicMock()
    mock_result_twin.scalar_one_or_none.return_value = mock_twin

    mock_db_session.execute.return_value = mock_result_twin

    async def mock_refresh(obj):
        obj.id = 5
        obj.created_at = datetime(2023, 1, 1)
        obj.status = "queued"
    mock_db_session.refresh.side_effect = mock_refresh

    # Patch the background task function to avoid real DB connection
    with patch("src.api.v1.twins.run_simulation_background", new_callable=AsyncMock) as mock_bg:
        response = await client.post(f"/api/v1/twins/{twin_id}/simulate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 5
        assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_get_history(client, mock_db_session):
    twin_id = 1

    mock_state = TwinState(id=10, twin_id=twin_id, state_data={"temp": 20}, simulation_mode="real", timestamp=datetime(2023, 1, 1))

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_state]
    mock_db_session.execute.return_value = mock_result

    response = await client.get(f"/api/v1/twins/{twin_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["state_data"]["temp"] == 20
