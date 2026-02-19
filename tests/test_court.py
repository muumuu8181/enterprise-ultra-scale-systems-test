import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.database import Base, get_db
from src.main import app
from src.models.court_models import Case, CaseType, CaseStatus
from datetime import datetime

# In-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_court_workflow():
    # 1. Create a Case directly in DB (since no POST /cases endpoint)
    async with TestingSessionLocal() as session:
        case = Case(
            case_number="CASE-001",
            case_type=CaseType.CIVIL,
            plaintiff="Alice",
            defendant="Bob",
            judge_id=1,
            court_id=101,
            filed_date=datetime.utcnow()
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        case_id = case.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 2. Get Cases
        response = await ac.get("/api/v1/cases")
        assert response.status_code == 200
        cases = response.json()
        assert len(cases) == 1
        assert cases[0]["case_number"] == "CASE-001"

        # 3. Schedule Hearing
        hearing_data = {
            "case_id": case_id,
            "hearing_type": "trial",
            "scheduled_at": "2023-12-01T09:00:00",
            "courtroom": "Room 101",
            "judge_id": 1,
            "duration_min": 120
        }
        response = await ac.post("/api/v1/hearings/schedule", json=hearing_data)
        assert response.status_code == 200
        hearing = response.json()
        assert hearing["status"] == "scheduled"

        # 4. File Document
        doc_data = {
            "case_id": case_id,
            "doc_type": "complaint",
            "filed_by": "Alice",
            "description": "Initial complaint",
            "file_url": "s3://bucket/doc.pdf",
            "sealed": False
        }
        response = await ac.post("/api/v1/documents/file", json=doc_data)
        assert response.status_code == 200
        doc = response.json()
        assert doc["doc_type"] == "complaint"

        # 5. Get Docket
        response = await ac.get(f"/api/v1/cases/{case_id}/docket")
        assert response.status_code == 200
        docket = response.json()
        assert docket["case"]["id"] == case_id
        assert len(docket["hearings"]) == 1
        assert len(docket["documents"]) == 1

        # 6. Judge Caseload
        response = await ac.get("/api/v1/judges/1/caseload")
        assert response.status_code == 200
        caseload = response.json()
        assert caseload["active_cases"] == 1
