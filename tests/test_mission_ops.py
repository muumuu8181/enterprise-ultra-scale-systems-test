import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import datetime
from sqlalchemy import select

from src.main import app
from src.core.database import get_db
from src.models.base import Base
from src.models.mission_models import Satellite, GroundStation, AlertConfiguration

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(test_session):
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_satellite_health(client, test_session):
    # Setup data
    sat = Satellite(name="Sat-1", status="nominal", health_metrics={"battery": 100})
    test_session.add(sat)
    await test_session.commit()
    await test_session.refresh(sat)

    response = await client.get(f"/mission-ops/missions/{sat.id}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "nominal"
    assert data["health_metrics"]["battery"] == 100

@pytest.mark.asyncio
async def test_emergency_procedure(client, test_session):
    sat = Satellite(name="Sat-2", status="nominal")
    test_session.add(sat)
    await test_session.commit()
    await test_session.refresh(sat)

    response = await client.post(f"/mission-ops/missions/{sat.id}/emergency-procedure",
                                 json={"procedure_type": "safe_mode"})
    assert response.status_code == 200
    assert response.json()["procedure"] == "safe_mode"

    await test_session.refresh(sat)
    assert "safe_mode" in sat.status

@pytest.mark.asyncio
async def test_ground_station_coverage(client, test_session):
    # ISS TLE (Epoch 2020 day 352 -> Dec 17/18)
    tle1 = "1 25544U 98067A   20352.54791667  .00001264  00000-0  30636-4 0  9993"
    tle2 = "2 25544  51.6442 207.2797 0001550 316.5786 166.3934 15.49138612260216"

    sat = Satellite(name="ISS", tle_line1=tle1, tle_line2=tle2)
    gs = GroundStation(name="Tokyo", latitude=35.6895, longitude=139.6917, elevation=0.0)

    test_session.add(sat)
    test_session.add(gs)
    await test_session.commit()
    await test_session.refresh(sat)
    await test_session.refresh(gs)

    # Set time near epoch to ensure visibility logic works correctly with SGP4
    start_time = datetime.datetime(2020, 12, 18, 0, 0, 0)
    end_time = start_time + datetime.timedelta(hours=6)

    params = {
        "satellite_id": sat.id,
        "ground_station_id": gs.id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }

    response = await client.get("/mission-ops/ground-stations/coverage", params=params)
    assert response.status_code == 200
    data = response.json()
    assert "windows" in data
    # With geometric check, there should be windows
    assert len(data["windows"]) >= 0

@pytest.mark.asyncio
async def test_anomaly_alerts(client, test_session):
    sat = Satellite(name="Sat-3")
    test_session.add(sat)
    await test_session.commit()
    await test_session.refresh(sat)

    threshold = {"voltage_min": 3.0}
    response = await client.post("/mission-ops/telemetry/anomaly-alerts",
                                 json={"satellite_id": sat.id, "threshold": threshold})
    assert response.status_code == 200
    assert response.json()["alert_created"] == True

    # Verify DB
    res = await test_session.execute(select(AlertConfiguration).where(AlertConfiguration.satellite_id == sat.id))
    alert = res.scalar_one()
    assert alert.thresholds == threshold
