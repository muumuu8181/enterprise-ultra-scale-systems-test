import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.main import app
from src.core.database import Base, get_db
from src.models.investigation import FraudCase, FraudCaseStatus

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_fraud_case():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/cases/open",
            json={
                "transaction_ids": ["tx_1", "tx_2"],
                "case_type": "account_takeover",
                "estimated_loss": 1500.00
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_ids"] == ["tx_1", "tx_2"]
    assert data["case_type"] == "account_takeover"
    assert data["status"] == "open"
    assert data["estimated_loss"] == 1500.0

@pytest.mark.asyncio
async def test_get_fraud_losses():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/fraud-losses?period=month")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "month"
    assert "fraud_loss_rate" in data

@pytest.mark.asyncio
async def test_add_note():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First create a case
        create_response = await ac.post(
            "/api/v1/cases/open",
            json={
                "transaction_ids": ["tx_3"],
                "case_type": "payment_fraud",
                "estimated_loss": 500.0
            }
        )
        case_id = create_response.json()["id"]

        # Add note
        response = await ac.post(
            f"/api/v1/cases/{case_id}/notes",
            json={
                "investigator_id": "inv_001",
                "note": "Suspicious activity detected.",
                "evidence": {"ip": "1.2.3.4"},
                "action_taken": "flagged"
            }
        )
        assert response.status_code == 200
        assert response.json() == {"status": "Note added"}

        # Verify timeline
        timeline_response = await ac.get(f"/api/v1/cases/{case_id}/timeline")
        assert timeline_response.status_code == 200
        notes = timeline_response.json()
        assert len(notes) == 1
        assert notes[0]["note"] == "Suspicious activity detected."
