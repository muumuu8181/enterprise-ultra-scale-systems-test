import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from datetime import datetime, timezone, timedelta

from src.models.v2x_models import Base
from src.models.intersection_models import IntersectionReservation
from src.api.v1.intersection import router, get_db

# In-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Create only the relevant table to avoid GeoAlchemy/Spatialite issues with SQLite
        await conn.run_sync(IntersectionReservation.__table__.create)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def app(db_session):
    app = FastAPI()
    app.include_router(router)

    # Override the get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_vehicle_enter(client):
    payload = {
        "vehicle_id": "v1",
        "speed": 15.0,
        "heading": 90.0
    }
    response = await client.post("/intersection/1/vehicles/enter", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "notified"

@pytest.mark.asyncio
async def test_make_reservation(client):
    now = datetime.now(timezone.utc)
    payload = {
        "vehicle_id": "v1",
        "arrival_time": now.isoformat(),
        "speed": 10.0,
        "heading": 0.0,
        "duration_seconds": 2.0
    }
    response = await client.post("/intersection/1/reservation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == "v1"
    assert data["intersection_id"] == 1

    # Check slots
    resp = await client.get("/intersection/1/reservation/slots")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

@pytest.mark.asyncio
async def test_conflict_detection(client):
    now = datetime.now(timezone.utc)
    payload1 = {
        "vehicle_id": "v1",
        "arrival_time": now.isoformat(),
        "duration_seconds": 5.0
    }
    # First reservation
    await client.post("/intersection/1/reservation", json=payload1)

    # Conflicting reservation (starts 2 seconds later, so overlaps)
    payload2 = {
        "vehicle_id": "v2",
        "arrival_time": (now + timedelta(seconds=2)).isoformat(),
        "duration_seconds": 5.0
    }
    response = await client.post("/intersection/1/reservation", json=payload2)
    assert response.status_code == 409

    # Non-conflicting reservation (starts 6 seconds later)
    payload3 = {
        "vehicle_id": "v3",
        "arrival_time": (now + timedelta(seconds=6)).isoformat(),
        "duration_seconds": 5.0
    }
    response = await client.post("/intersection/1/reservation", json=payload3)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_priority_listing(client):
    now = datetime.now(timezone.utc)

    # Normal vehicle arrives first
    await client.post("/intersection/1/reservation", json={
        "vehicle_id": "normal1",
        "arrival_time": now.isoformat(),
        "duration_seconds": 2.0,
        "priority": False
    })

    # Emergency vehicle arrives later
    await client.post("/intersection/1/reservation", json={
        "vehicle_id": "emg1",
        "arrival_time": (now + timedelta(seconds=10)).isoformat(),
        "duration_seconds": 2.0,
        "priority": True
    })

    # Test FCFS
    resp = await client.get("/intersection/1/reservation/slots?mode=fcfs")
    data = resp.json()
    assert data[0]["vehicle_id"] == "normal1"
    assert data[1]["vehicle_id"] == "emg1"

    # Test Priority
    resp = await client.get("/intersection/1/reservation/slots?mode=priority")
    data = resp.json()
    assert data[0]["vehicle_id"] == "emg1" # Should be first due to priority
    assert data[1]["vehicle_id"] == "normal1"

@pytest.mark.asyncio
async def test_delete_reservation(client):
    now = datetime.now(timezone.utc)
    payload = {
        "vehicle_id": "v_del",
        "arrival_time": now.isoformat()
    }
    resp = await client.post("/intersection/1/reservation", json=payload)
    res_id = resp.json()["id"]

    # Delete
    del_resp = await client.delete(f"/intersection/1/reservation/{res_id}")
    assert del_resp.status_code == 200

    # Verify gone
    get_resp = await client.get("/intersection/1/reservation/slots")
    assert len(get_resp.json()) == 0

    # Delete non-existent
    del_resp_bad = await client.delete(f"/intersection/1/reservation/999")
    assert del_resp_bad.status_code == 404
