import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from unittest.mock import AsyncMock, MagicMock
from src.database import get_db
from src.models.bee_models import Apiary
from datetime import datetime

@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Bee Colony Monitoring Platform API"}

@pytest.mark.asyncio
async def test_get_apiaries_mock():
    mock_session = AsyncMock()
    mock_result = MagicMock()

    # Create a mock Apiary object
    # We need to ensure attributes expected by Pydantic schema are present
    mock_apiary = Apiary()
    mock_apiary.id = 1
    mock_apiary.name = "Mock Apiary"
    mock_apiary.owner_id = 101
    mock_apiary.hive_count = 5
    mock_apiary.location = "POINT(0 0)" # WKBElement or string, Pydantic with arbitrary_types_allowed should pass it
    mock_apiary.registered_since = datetime.utcnow()
    mock_apiary.primary_forage = "Clover"
    mock_apiary.altitude_m = 100.0
    mock_apiary.climate_zone = "Temperate"

    mock_result.scalars.return_value.all.return_value = [mock_apiary]
    mock_session.execute.return_value = mock_result

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/apiaries")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Mock Apiary"

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_analytics_endpoint():
     transport = ASGITransport(app=app)
     async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/colony-loss-rate")
     assert response.status_code == 200
     assert response.json()["region"] == "global"
