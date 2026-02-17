import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.cctv_models import CCTVCamera, CCTVAnalytics, CCTVIncident
from unittest.mock import AsyncMock, MagicMock

# Test setup
@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
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
async def test_create_camera(client, mock_db_session):
    payload = {
        "camera_id": "cam-001",
        "latitude": 35.6895,
        "longitude": 139.6917,
        "status": "active",
        "stream_url": "rtsp://example.com/stream"
    }

    async def mock_refresh(obj):
        obj.id = 1
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/cctv/cameras", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "cam-001"
    assert data["id"] == 1
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_stream_url(client, mock_db_session):
    mock_camera = CCTVCamera(id=1, camera_id="cam-001", stream_url="rtsp://test")
    mock_db_session.get.return_value = mock_camera

    response = await client.get("/api/v1/cctv/cameras/1/stream")
    assert response.status_code == 200
    assert response.json()["stream_url"] == "rtsp://test"

@pytest.mark.asyncio
async def test_enable_analytics(client, mock_db_session):
    mock_camera = CCTVCamera(id=1, camera_id="cam-001", enabled_analytics={})
    mock_db_session.get.return_value = mock_camera

    payload = {"features": {"face_detection": True}}
    response = await client.post("/api/v1/cctv/cameras/1/analytics/enable", json=payload)
    assert response.status_code == 200
    assert response.json()["enabled_analytics"]["face_detection"] is True
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_report_incident(client, mock_db_session):
    mock_camera = CCTVCamera(id=1, camera_id="cam-001")
    mock_db_session.get.return_value = mock_camera

    async def mock_refresh(obj):
        obj.id = 100
        obj.timestamp = "2023-01-01T00:00:00"
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "camera_id": 1,
        "type": "theft",
        "screenshot_url": "http://img.com/1.jpg"
    }
    response = await client.post("/api/v1/cctv/incidents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["incident_type"] == "theft"
    assert data["id"] == 100
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_analytics_stats(client, mock_db_session):
    mock_result = MagicMock()
    mock_analytics = CCTVAnalytics(
        id=1,
        camera_id=1,
        timestamp="2023-01-01T00:00:00",
        crowd_density=0.5,
        vehicle_count=10,
        anomaly_detected=False
    )
    mock_result.scalars.return_value.all.return_value = [mock_analytics]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/cctv/analytics/1/stats")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["crowd_density"] == 0.5
