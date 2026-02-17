import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.db.base import Base
from src.main import app
from src.db.session import get_db

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="module")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_register_trial(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/trials/register", json={
            "compound_id": "CMP-001",
            "phase": 1,
            "enrollment_target": 100,
            "primary_endpoint": "Safety",
            "start_date": "2023-01-01"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["compound_id"] == "CMP-001"
    assert "id" in data

@pytest.mark.asyncio
async def test_enroll_subject(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trial_res = await ac.post("/api/v1/trials/register", json={
            "compound_id": "CMP-002",
            "phase": 2,
            "enrollment_target": 50,
            "primary_endpoint": "Efficacy",
            "start_date": "2023-06-01"
        })
        trial_id = trial_res.json()["id"]

        response = await ac.post(f"/api/v1/trials/{trial_id}/subjects/enroll", json={
            "subject_code": "SUB-001",
            "age": 30,
            "sex": "M",
            "baseline_score": 10.0,
            "treatment_arm": "drug"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["subject_code"] == "SUB-001"
    assert data["trial_id"] == trial_id

@pytest.mark.asyncio
async def test_report_adverse_event(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trial_res = await ac.post("/api/v1/trials/register", json={
            "compound_id": "CMP-003",
            "phase": 3,
            "enrollment_target": 200,
            "primary_endpoint": "Survival",
            "start_date": "2024-01-01"
        })
        trial_id = trial_res.json()["id"]

        subject_res = await ac.post(f"/api/v1/trials/{trial_id}/subjects/enroll", json={
            "subject_code": "SUB-002",
            "age": 45,
            "sex": "F",
            "baseline_score": 8.5,
            "treatment_arm": "placebo"
        })
        subject_id = subject_res.json()["id"]

        response = await ac.post(f"/api/v1/subjects/{subject_id}/adverse-event", json={
            "subject_id": subject_id,
            "event_type": "Headache",
            "severity": "mild",
            "causality": "unlikely"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "Headache"

@pytest.mark.asyncio
async def test_biostats_endpoints(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trial_res = await ac.post("/api/v1/trials/register", json={
            "compound_id": "CMP-004",
            "phase": 1,
            "enrollment_target": 20,
            "primary_endpoint": "PK",
            "start_date": "2023-01-01"
        })
        trial_id = trial_res.json()["id"]

        # Test interim analysis
        res_interim = await ac.get(f"/api/v1/trials/{trial_id}/interim-analysis")
        assert res_interim.status_code == 200
        assert "median_survival" in res_interim.json()

        # Test statistical analysis
        res_stats = await ac.post(f"/api/v1/trials/{trial_id}/statistical-analysis", json={
            "effect_size": 0.5,
            "power": 0.8,
            "alpha": 0.05
        })
        assert res_stats.status_code == 200
        assert "required_sample_size" in res_stats.json()
