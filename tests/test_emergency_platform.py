import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.emergency_models import Incident, IncidentStatus, IncidentType
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
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
async def test_create_incident(client, mock_db_session):
    payload = {
        "incident_type": "fire",
        "latitude": 35.6895,
        "longitude": 139.6917,
        "severity": 5,
        "caller_info": {"name": "John Doe", "phone": "555-0199"}
    }

    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 1
        obj.created_at = "2023-01-01T00:00:00"
    mock_db_session.refresh.side_effect = mock_refresh

    # Mock auto_dispatch query result (no units available)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    response = await client.post("/api/v1/incidents/create", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == 1
    assert data["incident_type"] == "fire"
    assert data["status"] == "new"
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_incident_status(client, mock_db_session):
    mock_incident = Incident(
        id=1,
        incident_type=IncidentType.MEDICAL,
        status=IncidentStatus.RESPONDING,
        severity=3
    )
    mock_db_session.get.return_value = mock_incident

    response = await client.get("/api/v1/incidents/1/status")

    assert response.status_code == 200
    assert response.json() == {"status": "responding"}

@pytest.mark.asyncio
async def test_update_incident(client, mock_db_session):
    mock_incident = Incident(
        id=1,
        incident_type=IncidentType.POLICE,
        status=IncidentStatus.NEW,
        severity=2
    )
    mock_db_session.get.return_value = mock_incident

    payload = {"status": "dispatched", "severity": 4}
    response = await client.post("/api/v1/incidents/1/update", json=payload)

    assert response.status_code == 200
    assert mock_incident.status == IncidentStatus.DISPATCHED
    assert mock_incident.severity == 4
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_close_incident(client, mock_db_session):
    mock_incident = Incident(
        id=1,
        incident_type=IncidentType.DISASTER,
        status=IncidentStatus.RESPONDING
    )
    mock_db_session.get.return_value = mock_incident

    response = await client.post("/api/v1/incidents/1/close")

    assert response.status_code == 200
    assert mock_incident.status == IncidentStatus.RESOLVED
    assert mock_db_session.commit.called
