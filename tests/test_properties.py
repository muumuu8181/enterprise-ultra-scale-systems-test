import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.database import get_db
from src.models.property_models import Property

client = TestClient(app)

# Mock DB session
mock_session = AsyncMock()

async def override_get_db():
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_mocks():
    mock_session.reset_mock()
    # Mock execute result
    mock_result = MagicMock()

    # Configure methods
    # db.add is synchronous
    mock_session.add = MagicMock()

    # db.commit, db.refresh, db.execute, db.get are async
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock()

    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None

def test_create_property():
    def side_effect_refresh(instance):
        instance.id = 1
    mock_session.refresh.side_effect = side_effect_refresh

    response = client.post("/api/v1/properties", json={
        "type": "apartment",
        "address": "123 Test St",
        "latitude": 35.6895,
        "longitude": 139.6917,
        "price": 50000000.0,
        "area_sqm": 50.5,
        "rooms": 2,
        "floor": 5,
        "year_built": 2020
    })

    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "123 Test St"
    assert data["id"] == 1

    assert mock_session.add.called
    assert mock_session.commit.called

    # Verify correct model creation
    args, _ = mock_session.add.call_args
    inserted_prop = args[0]
    assert isinstance(inserted_prop, Property)
    assert inserted_prop.address == "123 Test St"
    assert inserted_prop.location == "POINT(139.6917 35.6895)"

def test_get_properties():
    mock_prop = Property(
        id=1, type="apartment", address="123 Test St",
        price=50000000, area_sqm=50.5, rooms=2,
        location="POINT(139.6917 35.6895)"
    )
    mock_prop.media = []

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_prop]
    mock_session.execute.return_value = mock_result

    response = client.get("/api/v1/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["latitude"] == 35.6895

def test_get_property_detail():
    mock_prop = Property(
        id=1, type="apartment", address="123 Test St",
        price=50000000, area_sqm=50.5, rooms=2,
        location="POINT(139.6917 35.6895)"
    )
    mock_prop.media = []

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_prop
    mock_session.execute.return_value = mock_result

    response = client.get("/api/v1/properties/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_add_media():
    mock_prop = Property(
        id=1, type="commercial", address="789 Biz Blvd",
        price=100000000, area_sqm=200, rooms=1
    )

    # Mock select property for checking existence
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_prop
    mock_session.execute.return_value = mock_result

    # Set ID on refresh
    def side_effect_refresh(instance):
        instance.id = 100
    mock_session.refresh.side_effect = side_effect_refresh

    response = client.post("/api/v1/properties/1/media", json={
        "media_type": "photo",
        "url": "http://example.com/photo.jpg",
        "order": 1
    })

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "http://example.com/photo.jpg"
    assert mock_session.add.called
    assert mock_session.commit.called
