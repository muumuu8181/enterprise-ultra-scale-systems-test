import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.parking_models import ParkingLot, ParkingSpace, ParkingReservation
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Test setup
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
async def test_get_parking_lots(client, mock_db_session):
    mock_lot = ParkingLot(id=1, name="Lot A", total_spaces=10, available_spaces=5, price_per_hour=500.0)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_lot]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/parking/lots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Lot A"

@pytest.mark.asyncio
async def test_get_lot_availability(client, mock_db_session):
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5 # 5 available spaces
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/parking/lots/1/availability")
    assert response.status_code == 200
    assert response.json() == 5

@pytest.mark.asyncio
async def test_create_reservation(client, mock_db_session):
    # Mock finding lot
    mock_lot = ParkingLot(id=1, name="Lot A", price_per_hour=100.0)
    # Mock finding available space
    mock_space = ParkingSpace(id=10, lot_id=1, space_number="A1", is_occupied=False)

    # execute is called twice: once for lot, once for space
    mock_result_lot = MagicMock()
    mock_result_lot.scalar_one_or_none.return_value = mock_lot

    mock_result_space = MagicMock()
    mock_result_space.scalars.return_value.first.return_value = mock_space

    mock_db_session.execute.side_effect = [mock_result_lot, mock_result_space]

    payload = {
        "lot_id": 1,
        "start_time": "2023-01-01T10:00:00",
        "duration_minutes": 60,
        "user_id": "user123"
    }

    # Mock refresh to set ID
    async def mock_refresh(obj):
        obj.id = 100
        obj.end_time = datetime(2023, 1, 1, 11, 0, 0)
        obj.fee = 100.0
    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/parking/reservations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 100
    assert data["fee"] == 100.0
    assert mock_db_session.add.called

@pytest.mark.asyncio
async def test_process_payment(client, mock_db_session):
    mock_reservation = ParkingReservation(id=100, fee=500.0)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_reservation
    mock_db_session.execute.return_value = mock_result

    response = await client.post("/api/v1/parking/payments/100")
    assert response.status_code == 200
    assert response.json()["message"] == "Payment successful"

@pytest.mark.asyncio
async def test_parking_guidance(client, mock_db_session):
    mock_lot = ParkingLot(id=1, name="Lot A", total_spaces=10, available_spaces=5, price_per_hour=500.0)
    distance = 150.0 # meters

    mock_result = MagicMock()
    mock_result.all.return_value = [(mock_lot, distance)]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/parking/guidance?destination=35.6895,139.6917")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lot"]["name"] == "Lot A"
    assert data[0]["distance_meters"] == 150.0
