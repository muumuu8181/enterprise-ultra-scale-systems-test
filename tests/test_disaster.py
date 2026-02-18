import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.disaster_models import DisasterEvent, EvacuationRoute, Shelter, DisasterType
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

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
async def test_create_event(client, mock_db_session):
    payload = {
        "type": "earthquake",
        "severity": "critical",
        "area_polygon": "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
    }

    async def mock_refresh(obj):
        obj.id = 1
        if not obj.started_at:
             obj.started_at = datetime.now(timezone.utc)
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/disaster/events", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "earthquake"
    assert data["severity"] == "critical"
    assert data["id"] == 1
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_active_events(client, mock_db_session):
    mock_result = MagicMock()
    mock_event = DisasterEvent(
        id=1,
        type=DisasterType.EARTHQUAKE,
        severity="critical",
        status="active",
        started_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    )
    # Mock scalars().all()
    mock_result.scalars.return_value.all.return_value = [mock_event]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/disaster/events/active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["type"] == "earthquake"

@pytest.mark.asyncio
async def test_create_evacuation_route(client, mock_db_session):
    # Mock finding the event
    mock_event = DisasterEvent(id=1, status="active")
    mock_db_session.get.return_value = mock_event

    payload = {
        "event_id": 1,
        "route_geojson": {"type": "LineString", "coordinates": [[0,0], [1,1]]},
        "priority": 1,
        "estimated_time_min": 10,
        "shelter_ids": [101, 102]
    }

    async def mock_refresh(obj):
        obj.id = 5
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/disaster/evacuations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 5
    assert data["shelter_ids"] == [101, 102]
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_get_shelters(client, mock_db_session):
    mock_result = MagicMock()
    mock_shelter = Shelter(
        id=1,
        name="Central Park Shelter",
        capacity=100,
        current_occupancy=50,
        facilities={"wifi": True}
    )
    mock_result.scalars.return_value.all.return_value = [mock_shelter]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/disaster/shelters")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Central Park Shelter"
    assert data[0]["capacity"] == 100

@pytest.mark.asyncio
async def test_update_occupancy(client, mock_db_session):
    mock_shelter = Shelter(
        id=1,
        name="Shelter A",
        capacity=100,
        current_occupancy=50,
        facilities={}
    )
    mock_db_session.get.return_value = mock_shelter

    payload = {"count": 60}
    response = await client.put("/api/v1/disaster/shelters/1/occupancy", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["current_occupancy"] == 60
    assert mock_shelter.current_occupancy == 60
