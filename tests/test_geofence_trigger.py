import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.routing_models import ETARequest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Helper to mock DB
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
async def test_update_eta_geofence_trigger(client, mock_db_session):
    """
    Test ETA update simulates a location update (geofence trigger)
    """
    # Mock existing ETARequest
    eta_id = 1
    mock_request = ETARequest(
        id=eta_id,
        user_id="user1",
        origin="LocA",
        destination="LocB",
        mode="driving",
        estimated_arrival=datetime.now(timezone.utc),
        requested_at=datetime.now(timezone.utc)
    )

    # Setup mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_request
    mock_db_session.execute.return_value = mock_result

    # Call update endpoint
    # Simulating moving to a new coordinate
    lat, lon = 35.6900, 139.6920
    response = await client.get(f"/api/v1/eta/{eta_id}/update?lat={lat}&lon={lon}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == eta_id
    assert "estimated_arrival" in data

    # Verify DB commit was called (meaning update happened)
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_eta_update_not_found(client, mock_db_session):
    # Mock empty result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/eta/999/update?lat=0&lon=0")
    assert response.status_code == 404
