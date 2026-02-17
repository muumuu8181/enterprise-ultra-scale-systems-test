import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from src.models.loan_models import Base, Loan, LoanRepayment, LoanStatus
from src.api.v1.loans import router, get_session
from src.services.loan_service import LoanService

# Use in-memory SQLite
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    app = FastAPI()
    app.include_router(router)

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    # Create transport for async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_apply_loan(client):
    response = await client.post("/loans/apply", json={
        "customer_id": 101,
        "amount": "12000",
        "term_months": 12,
        "purpose": "Car Loan",
        "interest_rate": "0.05"
    })
    assert response.status_code == 201
    data = response.json()
    assert float(data["amount"]) == 12000.00
    assert data["term_months"] == 12
    assert data["status"] == "PENDING"
    assert "id" in data

@pytest.mark.asyncio
async def test_approve_loan(client, db_session):
    # Setup - use Decimal explicitly for creating
    loan = await LoanService.create_loan(db_session, 101, Decimal("12000"), Decimal("0.05"), 12, "Test")

    response = await client.put(f"/loans/{loan.id}/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["approved_at"] is not None

    # Verify schedule
    sched_resp = await client.get(f"/loans/schedule/{loan.id}")
    assert sched_resp.status_code == 200
    schedule = sched_resp.json()
    assert len(schedule) == 12
    # Check first payment amount roughly correct
    # P=12000, r=0.05/12, n=12. PMT ~ 1027.29
    assert schedule[0]["amount"] == "1027.29"

@pytest.mark.asyncio
async def test_repay_loan_exact_installment(client, db_session):
    loan = await LoanService.create_loan(db_session, 101, Decimal("1000"), Decimal("0.0"), 2, "Test")
    await LoanService.approve_loan(db_session, loan.id)

    # Check schedule
    sched_resp = await client.get(f"/loans/schedule/{loan.id}")
    payment_amount = sched_resp.json()[0]["amount"]
    assert payment_amount == "500.00"

    # Pay exact amount
    response = await client.post(f"/loans/{loan.id}/repay", json={"amount": "500.00"})
    assert response.status_code == 200

    # Check schedule again
    response = await client.get(f"/loans/schedule/{loan.id}")
    schedule_data = response.json()
    assert schedule_data[0]["paid_at"] is not None
    assert schedule_data[1]["paid_at"] is None

@pytest.mark.asyncio
async def test_repay_loan_full(client, db_session):
    loan = await LoanService.create_loan(db_session, 101, Decimal("1000"), Decimal("0.0"), 2, "Test")
    await LoanService.approve_loan(db_session, loan.id)

    # Pay all (500 + 500)
    response = await client.post(f"/loans/{loan.id}/repay", json={"amount": "1000.00"})
    assert response.status_code == 200

    # Check status
    loan_resp = await client.get(f"/loans/{loan.id}")
    assert loan_resp.json()["status"] == "PAID_OFF"

@pytest.mark.asyncio
async def test_repay_loan_invalid_amounts(client, db_session):
    loan = await LoanService.create_loan(db_session, 101, Decimal("1000"), Decimal("0.0"), 2, "Test")
    await LoanService.approve_loan(db_session, loan.id)
    # Installments are 500 each

    # Underpayment
    response = await client.post(f"/loans/{loan.id}/repay", json={"amount": "400.00"})
    assert response.status_code == 400
    assert "exact" in response.json()["detail"] or "installment" in response.json()["detail"]

    # Overpayment (for one installment)
    response = await client.post(f"/loans/{loan.id}/repay", json={"amount": "600.00"})
    assert response.status_code == 400

    # Partial payment for second installment (pay 1.5 installments)
    response = await client.post(f"/loans/{loan.id}/repay", json={"amount": "750.00"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_delinquency_check(db_session):
    # Manually test service method
    loan = await LoanService.create_loan(db_session, 101, Decimal("1000"), Decimal("0.0"), 1, "Test")
    await LoanService.approve_loan(db_session, loan.id)

    schedule = await LoanService.get_repayment_schedule(db_session, loan.id)
    repayment = schedule[0]

    # Make it overdue
    repayment.due_date = date.today() - timedelta(days=1)
    db_session.add(repayment)
    await db_session.commit()

    is_delinquent = await LoanService.check_delinquency(db_session, loan.id)
    assert is_delinquent is True

    await db_session.refresh(loan)
    assert loan.status == LoanStatus.DEFAULTED
