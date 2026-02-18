import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.citizen_models import CitizenReport, ServiceAppointment
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
async def test_create_report_success(client, mock_db_session):
    payload = {
        "category": "road_damage",
        "description": "Big pothole",
        "latitude": 35.6895,
        "longitude": 139.6917,
        "photos": ["http://example.com/photo.jpg"]
    }

    # Mock refresh to set ID and default values
    async def mock_refresh(obj):
        obj.id = 1
        if not hasattr(obj, 'status') or obj.status is None:
            obj.status = "Pending"
        if not hasattr(obj, 'created_at') or obj.created_at is None:
            obj.created_at = "2023-01-01T00:00:00"
    mock_db_session.refresh.side_effect = mock_refresh

    # Patch notify_citizen to avoid actual print/log
    with patch("src.api.v1.citizen_portal.notify_citizen", new_callable=AsyncMock) as mock_notify:
        response = await client.post("/api/v1/citizen/reports", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "road_damage"
        assert data["id"] == 1
        assert data["assigned_dept"] == "Road Maintenance Dept" # Auto assigned
        assert mock_db_session.add.called
        assert mock_notify.called

@pytest.mark.asyncio
async def test_get_report_status_success(client, mock_db_session):
    # Mock DB result
    mock_result = MagicMock()
    mock_report = CitizenReport(
        id=1,
        category="road_damage",
        description="test",
        status="In Progress",
        assigned_dept="Road Maintenance Dept"
    )
    mock_result.scalars.return_value.first.return_value = mock_report
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/citizen/reports/1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "In Progress"
    assert data["assigned_dept"] == "Road Maintenance Dept"

@pytest.mark.asyncio
async def test_create_appointment_success(client, mock_db_session):
    payload = {
        "service_id": "residency_cert",
        "citizen_id": "user123",
        "scheduled_at": "2023-12-01T10:00:00"
    }

    # Mock count query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [] # Count = 0
    mock_db_session.execute.return_value = mock_result

    async def mock_refresh(obj):
        obj.id = 1
        if not hasattr(obj, 'queue_number'):
            obj.queue_number = 1
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/citizen/appointments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["queue_number"] == 1
    assert data["status"] == "Scheduled"
