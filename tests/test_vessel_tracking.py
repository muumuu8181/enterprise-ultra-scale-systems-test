import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from src.services import ais_service
from src.models.vessel_models import Vessel, AISPosition, Port, VesselType
from src.api.v1.vessels import router, get_db
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from shapely.geometry import Point as ShapelyPoint

# Mock FastAPI app
app = FastAPI()
app.include_router(router)

@pytest.mark.asyncio
async def test_ingest_ais_stream():
    messages = [{
        "mmsi": 123456789,
        "vessel_name": "Test Vessel",
        "vessel_type": "cargo",
        "latitude": 35.0,
        "longitude": 139.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "speed_knots": 10.0,
        "course": 180.0
    }]

    mock_session = AsyncMock()
    # Configure synchronous methods
    mock_session.add = MagicMock()

    # Mock execute result for vessel lookup (return None -> not found)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # We need to support nested context manager: async with AsyncSessionLocal() as session:
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("src.services.ais_service.AsyncSessionLocal", return_value=mock_session):
        count = await ais_service.ingest_ais_stream(messages)

    assert count == 1
    # Verify vessel added. session.add called for Vessel and AISPosition
    assert mock_session.add.call_count == 2

@pytest.mark.asyncio
async def test_predict_eta():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Mock last position
    last_pos = AISPosition(
        latitude=35.0, longitude=139.0,
        speed_knots=10.0, timestamp=datetime.now(timezone.utc)
    )

    # Mock port
    mock_port = Port(id=1, location="POINT(140.0 35.0)")

    # Mocking returns
    mock_result_pos = MagicMock()
    mock_result_pos.scalar_one_or_none.return_value = last_pos

    mock_result_port = MagicMock()
    mock_result_port.scalar_one_or_none.return_value = mock_port

    mock_session.execute.side_effect = [mock_result_pos, mock_result_port]

    with patch("src.services.ais_service.AsyncSessionLocal", return_value=mock_session), \
         patch("src.services.ais_service.to_shape") as mock_to_shape:

        mock_to_shape.return_value = ShapelyPoint(140.0, 35.0)

        eta = await ais_service.predict_eta(1, 1)

        assert eta is not None
        assert eta > last_pos.timestamp

@pytest.mark.asyncio
async def test_detect_dark_ship():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Mock positions with a gap > 2 hours
    now = datetime.now(timezone.utc)
    pos1 = AISPosition(timestamp=now - timedelta(hours=5), latitude=0, longitude=0)
    pos2 = AISPosition(timestamp=now - timedelta(hours=1), latitude=0, longitude=0)
    # Gap is 4 hours

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [pos1, pos2]
    mock_session.execute.return_value = mock_result

    with patch("src.services.ais_service.AsyncSessionLocal", return_value=mock_session):
        alert = await ais_service.detect_dark_ship(1)

        assert alert is not None
        assert alert.vessel_id == 1
        assert alert.severity == "medium"
        assert alert.gap_start == pos1.timestamp
        assert alert.gap_end == pos2.timestamp

@pytest.mark.asyncio
async def test_api_search_vessels():
    # Mock get_db dependency
    mock_db = AsyncMock()
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    # Mock result
    mock_vessel = Vessel(id=1, mmsi=123, vessel_name="Test", vessel_type=VesselType.CARGO, flag_country="JP", length_m=100, gross_tonnage=1000, owner_id=1)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_vessel]
    mock_db.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/vessels/search?name=Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["vessel_name"] == "Test"
