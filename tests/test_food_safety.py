import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.food_safety_models import FoodFacility, Inspection, Violation
from unittest.mock import AsyncMock, MagicMock

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
async def test_get_facilities(client, mock_db_session):
    # Mock return value
    mock_facility = FoodFacility(
        id=1, name="Test Restaurant", facility_type="restaurant",
        address="123 Test St", license_number="L123", risk_category="low",
        status="active"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_facility]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/food-safety/facilities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Restaurant"

@pytest.mark.asyncio
async def test_schedule_inspection(client, mock_db_session):
    # Mock facility check
    mock_facility = FoodFacility(id=1, name="Test")
    mock_result = MagicMock()
    # First call checks facility existence
    mock_result.scalar.return_value = mock_facility
    mock_db_session.execute.return_value = mock_result

    # Mock refresh to set ID on new inspection
    async def mock_refresh(obj):
        obj.id = 101
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "facility_id": 1,
        "inspector_id": "INS-001",
        "inspection_type": "routine",
        "date": "2023-10-27T10:00:00"
    }

    response = await client.post("/api/v1/food-safety/inspections/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 101
    assert data["inspector_id"] == "INS-001"
    assert mock_db_session.add.called
