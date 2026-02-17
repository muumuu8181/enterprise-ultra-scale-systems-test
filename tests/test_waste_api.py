import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.waste_models import WasteBin, CollectionRoute
from unittest.mock import AsyncMock, MagicMock
from geoalchemy2.elements import WKTElement
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
async def test_get_bins(client, mock_db_session):
    # Mock data
    mock_bin = WasteBin(
        id=1,
        location=WKTElement("POINT(139.7 35.7)", srid=4326),
        district="Shibuya",
        bin_type="burnable",
        capacity_liters=100,
        fill_level=50.0,
        last_collected=datetime.utcnow()
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_bin]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/waste/bins")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    # Check location serialization
    assert data[0]["location"] == {"lat": 35.7, "lon": 139.7}

@pytest.mark.asyncio
async def test_update_fill_level(client, mock_db_session):
    mock_bin = WasteBin(
        id=1,
        fill_level=20.0,
        location=WKTElement("POINT(0 0)", srid=4326),
        district="Test",
        bin_type="test",
        capacity_liters=100,
        last_collected=datetime.utcnow()
    )
    mock_db_session.get.return_value = mock_bin

    # Mock refresh to keep object valid or verify call
    async def mock_refresh(obj):
        pass
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.put("/api/v1/waste/bins/1/fill-level", json={"fill_level": 80.0})
    assert response.status_code == 200
    assert response.json()["fill_level"] == 80.0
    assert mock_bin.fill_level == 80.0
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_optimize_route(client, mock_db_session):
    # Mock multiple bins
    bins = [
        WasteBin(id=1, location=WKTElement("POINT(139.70 35.68)", srid=4326), district="D1"),
        WasteBin(id=2, location=WKTElement("POINT(139.71 35.68)", srid=4326), district="D1"),
        WasteBin(id=3, location=WKTElement("POINT(139.70 35.69)", srid=4326), district="D1")
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = bins
    mock_db_session.execute.return_value = mock_result

    # Setup refresh for the new route
    async def mock_refresh(obj):
        obj.id = 100 # Assign mock ID
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {"district": "D1", "driver_id": "driver-1"}
    response = await client.post("/api/v1/waste/collection/optimize", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["waypoints"]) == 3
    assert data["driver_id"] == "driver-1"
    assert data["total_distance_km"] > 0
    assert data["id"] == 100

    # Check if saved to DB
    assert mock_db_session.add.called
    args, _ = mock_db_session.add.call_args
    saved_route = args[0]
    assert isinstance(saved_route, CollectionRoute)
    assert saved_route.driver_id == "driver-1"

@pytest.mark.asyncio
async def test_get_routes(client, mock_db_session):
    mock_route = CollectionRoute(
        id=1,
        driver_id="d1",
        waypoints=[],
        total_distance_km=10.0,
        estimated_duration_min=30.0,
        date=datetime.utcnow()
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_route]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/waste/collection/routes")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["driver_id"] == "d1"
