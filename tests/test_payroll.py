import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date

from src.core.database import Base, get_db
from src.models.hr_models import Employee, Payroll
from src.api.v1.payroll import router as payroll_router
from src.api.v1.performance import router as performance_router

# Test database setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Seed data
        emp = Employee(
            name="Test Employee",
            department="Engineering",
            base_salary=500000.0,
            joined_date=date(2023, 1, 1),
            bank_account_number="123456789"
        )
        session.add(emp)
        await session.commit()
        await session.refresh(emp)
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def app_client(db_session):
    app = FastAPI()
    app.include_router(payroll_router, prefix="/api/v1")
    app.include_router(performance_router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_calculate_payroll(app_client):
    response = await app_client.post("/api/v1/payroll/calculate/2023-10", json={"employee_id": 1, "overtime_hours": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == 1
    assert data["month"] == "2023-10"
    assert data["basic_salary"] == 500000.0
    # Overtime: (500000 / 160) * 1.5 * 10 = 3125 * 1.5 * 10 = 46875
    assert data["overtime_pay"] == 46875.0
    assert data["status"] == "PROCESSED"

@pytest.mark.asyncio
async def test_get_payslip(app_client):
    # First calculate
    await app_client.post("/api/v1/payroll/calculate/2023-10", json={"employee_id": 1})

    response = await app_client.get("/api/v1/payroll/1/2023-10")
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == 1

@pytest.mark.asyncio
async def test_performance_review(app_client):
    review_data = {
        "employee_id": 1,
        "period": "2023-H1",
        "ratings": {"technical": 5, "communication": 4},
        "comments": "Great work"
    }
    response = await app_client.post("/api/v1/performance/reviews", json=review_data)
    assert response.status_code == 200
    data = response.json()
    assert data["comments"] == "Great work"

    # Get history
    hist_response = await app_client.get("/api/v1/performance/1/history")
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert len(hist_data) == 1
    assert hist_data[0]["period"] == "2023-H1"

@pytest.mark.asyncio
async def test_performance_goals(app_client):
    goals_data = {
        "employee_id": 1,
        "goals": [
            {"description": "Learn Rust", "deadline": "2023-12-31"},
            {"description": "Ship feature X", "deadline": "2023-11-30"}
        ]
    }
    response = await app_client.post("/api/v1/performance/goals", json=goals_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["description"] == "Learn Rust"
