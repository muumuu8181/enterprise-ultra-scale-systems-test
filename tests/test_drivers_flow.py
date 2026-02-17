import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.api.v1.drivers import router
from src.core.database import get_db
from src.models.driver_models import Driver, DriverStatus
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.fixture
def mock_driver(mock_db_session):
    driver = MagicMock(spec=Driver)
    driver.id = 1
    driver.status = DriverStatus.offline
    driver.current_location = None

    # Configure session to return this driver
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = driver
    mock_db_session.execute.return_value = mock_result
    return driver

@pytest.mark.asyncio
async def test_go_online(app, mock_db_session, mock_driver):
    app.dependency_overrides[get_db] = lambda: mock_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/drivers/go-online", params={"driver_id": 1}, json={"status": "online"})

    assert response.status_code == 200
    assert response.json()["new_status"] == "online"
    # Verify the driver object was updated
    assert mock_driver.status == "online"

@pytest.mark.asyncio
async def test_update_location(app, mock_db_session, mock_driver):
    app.dependency_overrides[get_db] = lambda: mock_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/drivers/update-location", params={"driver_id": 1}, json={"latitude": 35.6895, "longitude": 139.6917})

    assert response.status_code == 200
    assert "POINT(139.6917 35.6895)" in mock_driver.current_location
