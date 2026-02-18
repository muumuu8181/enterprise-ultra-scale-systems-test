import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.location_models import UserLocation, GeofenceZone, GeofenceEvent
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

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
async def test_update_locations(client, mock_db_session):
    payload = [
        {"user_id": "u1", "latitude": 35.0, "longitude": 139.0, "accuracy_m": 10.0}
    ]

    # Patch check_geofences to avoid complex logic in integration test
    with patch("src.services.geofence_service.check_geofences", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = []

        response = await client.post("/api/v1/locations/update", json=payload)
        assert response.status_code == 200
        assert mock_db_session.add.called
        assert mock_check.called

@pytest.mark.asyncio
async def test_create_geofence(client, mock_db_session):
    async def mock_refresh(obj):
        obj.id = 1
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "name": "Central Park",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]
        },
        "zone_type": "polygon"
    }

    response = await client.post("/api/v1/geofences/create", json=payload)
    assert response.status_code == 200
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_check_geofences_logic_enter(mock_db_session):
    # Test service logic directly with mocked DB results
    from src.services.geofence_service import check_geofences
    from src.models.location_models import GeofenceZone, GeofenceEvent

    # Setup mock return for "current zones"
    mock_result_zones = MagicMock()
    zone = GeofenceZone(id=1, name="Zone1", trigger_on="enter,exit", zone_type="polygon", dwell_seconds=60)
    mock_result_zones.scalars.return_value.all.return_value = [zone]

    # Setup mock return for "last events"
    mock_result_events = MagicMock()
    mock_result_events.scalars.return_value.all.return_value = [] # No previous events

    # We need to control the sequence of db.execute calls
    # 1. Select zones (contains point)
    # 2. Select last events
    # Note: check_geofences calls execute twice.
    mock_db_session.execute.side_effect = [mock_result_zones, mock_result_events]

    events = await check_geofences(mock_db_session, "u1", 0.5, 0.5)

    assert len(events) == 1
    assert events[0].event_type == "enter"
    assert events[0].zone_id == 1

@pytest.mark.asyncio
async def test_check_geofences_logic_exit(mock_db_session):
    from src.services.geofence_service import check_geofences
    from src.models.location_models import GeofenceZone, GeofenceEvent

    # User is NOT in any zone currently
    mock_result_zones = MagicMock()
    mock_result_zones.scalars.return_value.all.return_value = []

    # But WAS in Zone1 (enter)
    mock_result_events = MagicMock()
    last_event = GeofenceEvent(id=10, user_id="u1", zone_id=1, event_type="enter", triggered_at=datetime.utcnow())
    mock_result_events.scalars.return_value.all.return_value = [last_event]

    # Logic needs to fetch the zone to check trigger_on
    mock_result_zone_fetch = MagicMock()
    zone = GeofenceZone(id=1, name="Zone1", trigger_on="enter,exit", zone_type="polygon")
    mock_result_zone_fetch.scalar_one_or_none.return_value = zone

    mock_db_session.execute.side_effect = [mock_result_zones, mock_result_events, mock_result_zone_fetch]

    events = await check_geofences(mock_db_session, "u1", 0.5, 0.5)

    assert len(events) == 1
    assert events[0].event_type == "exit"
    assert events[0].zone_id == 1
