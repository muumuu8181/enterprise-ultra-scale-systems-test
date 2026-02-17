import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.api.v1.ev import router
from src.database import get_db
from src.models.ev_charging import EVCharger, ChargingSession, ChargerStatus, ConnectorType
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, AsyncMock

app = FastAPI()
app.include_router(router)

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)

    # Mock for get_available_chargers
    charger_avail = EVCharger(
        id=1,
        site_id=101,
        connector_type=ConnectorType.CCS,
        max_kw=50.0,
        status=ChargerStatus.AVAILABLE
    )

    # Mock result proxy for execute
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [charger_avail]
    mock_result.scalars.return_value.first.return_value = None # Default
    session.execute.return_value = mock_result

    # Mock get
    session.get = AsyncMock()
    session.get.return_value = charger_avail

    return session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _get_db():
        yield mock_db_session
    return _get_db

@pytest.mark.asyncio
async def test_get_available_chargers(override_get_db, mock_db_session):
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/chargers/available")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["status"] == "available"

@pytest.mark.asyncio
async def test_start_session(override_get_db, mock_db_session):
    app.dependency_overrides[get_db] = override_get_db

    # Mock charger
    charger = EVCharger(
        id=1,
        site_id=101,
        connector_type=ConnectorType.CCS,
        max_kw=50.0,
        status=ChargerStatus.AVAILABLE
    )
    mock_db_session.get.return_value = charger

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/chargers/1/start-session", json={"user_id": 1, "vehicle_id": 2})

    if response.status_code != 200:
        print(response.json())

    assert response.status_code == 200
    assert response.json()["status"] == "started"
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
