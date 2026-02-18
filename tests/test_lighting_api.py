import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.lighting_models import LightPole, LightingZone
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
async def test_create_pole(client, mock_db_session):
    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 1
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "pole_id": "P001",
        "latitude": 35.1,
        "longitude": 139.1,
        "zone_id": "Z1"
    }
    response = await client.post("/api/v1/lighting/poles", json=payload)
    assert response.status_code == 200
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_poles(client, mock_db_session):
    from datetime import datetime
    mock_pole = LightPole(
        id=1,
        pole_id="P001",
        brightness=50,
        status="active",
        zone_id="Z1",
        last_maintenance=datetime.utcnow()
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_pole]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/lighting/poles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["pole_id"] == "P001"

@pytest.mark.asyncio
async def test_set_brightness(client, mock_db_session):
    mock_pole = LightPole(id=1, pole_id="P001", brightness=50)
    mock_db_session.get.return_value = mock_pole

    payload = {"level": 80}
    response = await client.put("/api/v1/lighting/poles/1/brightness", json=payload)
    assert response.status_code == 200
    assert mock_pole.brightness == 80
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_set_schedule(client, mock_db_session):
    # Mock zone search returning None, implying creation
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    payload = {"schedule": {"08:00": 0, "18:00": 100}}
    response = await client.post("/api/v1/lighting/zones/Z1/schedule", json=payload)
    assert response.status_code == 200
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_set_motion_trigger(client, mock_db_session):
    mock_zone = LightingZone(id=1, zone_id="Z1", motion_trigger_enabled=False)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_zone
    mock_db_session.execute.return_value = mock_result

    payload = {"enabled": True}
    response = await client.post("/api/v1/lighting/zones/Z1/motion-trigger", json=payload)
    assert response.status_code == 200
    assert mock_zone.motion_trigger_enabled is True
