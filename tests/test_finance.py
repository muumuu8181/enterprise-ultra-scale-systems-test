import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.database import Base
from src.api.v1.accounts import router
from src.models.finance_models import Account, Transaction, AccountType, TransactionType

# Setup test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest.fixture(scope="module")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_db):
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def app_client(db_session):
    app = FastAPI()
    app.include_router(router)

    # Override get_db dependency
    from src.api.v1.accounts import get_db
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_connect_account(app_client):
    response = await app_client.post("/accounts/connect", json={
        "user_id": 1,
        "institution": "Chase",
        "account_name": "My Checking",
        "account_type": "checking"
    })
    assert response.status_code == 200
    data = response.json()
    assert "account_id" in data

@pytest.mark.asyncio
async def test_manual_account_entry(app_client):
    response = await app_client.post("/accounts/manual", json={
        "user_id": 1,
        "account_name": "Cash Stash",
        "account_type": "savings",
        "balance": 1000.0,
        "currency": "USD"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Account created manually"

@pytest.mark.asyncio
async def test_get_balance(app_client):
    # First create an account
    create_response = await app_client.post("/accounts/manual", json={
        "user_id": 2,
        "account_name": "Investment",
        "account_type": "investment",
        "balance": 5000.0
    })
    account_id = create_response.json()["account_id"]

    response = await app_client.get(f"/accounts/{account_id}/balance")
    assert response.status_code == 200
    assert response.json()["balance"] == 5000.0

@pytest.mark.asyncio
async def test_auto_categorize_service():
    from src.services.finance_service import auto_categorize
    from src.models.finance_models import Transaction

    t = Transaction(merchant="Starbucks Coffee", amount=5.0)
    category = await auto_categorize(t)
    assert category == "Food & Drink"

    t2 = Transaction(merchant="Unknown", amount=10.0)
    category2 = await auto_categorize(t2)
    assert category2 == "General"
