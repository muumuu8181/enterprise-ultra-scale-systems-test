import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.signage_models import SignageDevice, ContentPlaylist, Orientation
from src.api.v1.devices import router
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

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
async def test_register_device(client, mock_db_session):
    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 1
        if not obj.status:
             obj.status = "offline"
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "serial": "SIG-TEST-001",
        "latitude": 35.0,
        "longitude": 139.0,
        "screen_size": 42.0,
        "orientation": "portrait",
        "os_version": "1.0",
        "groups": ["test-group"]
    }
    response = await client.post("/api/v1/devices/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["serial"] == "SIG-TEST-001"
    assert data["groups"] == ["test-group"]
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_assign_playlist(client, mock_db_session):
    # Mock Playlist
    mock_playlist = ContentPlaylist(id=10, name="Promo", target_device_groups=["test-group"])

    # Mock Device
    mock_device = SignageDevice(id=1, serial="D1", groups=["test-group"], status="online")

    # Mock Devices query (for selecting devices in group)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_db_session.execute.return_value = mock_result

    # Mock db.get calls
    async def get_side_effect(model, id):
        if model == ContentPlaylist and id == 10:
            return mock_playlist
        if model == SignageDevice and id == 1:
            return mock_device
        return None
    mock_db_session.get.side_effect = get_side_effect

    payload = {
        "group_name": "test-group",
        "playlist_id": 10
    }

    response = await client.post("/api/v1/devices/groups/assign-playlist", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Assigned playlist to 1 devices" in data["message"]
    assert data["details"][0]["status"] == "success"
