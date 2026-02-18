import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
from sqlalchemy.orm import selectinload

from src.main import app
from src.models.base import Base
from src.models.openbanking_models import BankConnection, BankAccount, Transaction, ConnectionStatus
from src.api.dependencies import get_db

# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

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

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_initiate_connection(async_client):
    payload = {
        "user_id": "user_123",
        "bank_name": "Test Bank",
        "public_token": "public_test_123"
    }
    response = await async_client.post("/connections/initiate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert data["status"] == "active"
    assert "id" in data

    # Verify connection created
    async with TestingSessionLocal() as session:
        conn = await session.get(BankConnection, data["id"], options=[selectinload(BankConnection.accounts)])
        assert conn is not None
        assert conn.user_id == "user_123"
        # Check if accounts were created (mock)
        assert len(conn.accounts) == 2

@pytest.mark.asyncio
async def test_list_connections(async_client):
    # Seed data
    async with TestingSessionLocal() as session:
        conn = BankConnection(
            user_id="user_list",
            bank_name="List Bank",
            access_token="token",
            status=ConnectionStatus.ACTIVE
        )
        session.add(conn)
        await session.commit()

    response = await async_client.get("/connections/list?user_id=user_list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["bank_name"] == "List Bank"

@pytest.mark.asyncio
async def test_get_transactions_sync(async_client):
    # Create connection and account
    async with TestingSessionLocal() as session:
        conn = BankConnection(
            user_id="user_tx",
            bank_name="Tx Bank",
            access_token="token",
            status=ConnectionStatus.ACTIVE
        )
        session.add(conn)
        await session.commit()
        await session.refresh(conn)

        acc = BankAccount(
            connection_id=conn.id,
            account_number_hash="hash",
            account_type="checking",
            balance=1000,
            currency="USD",
            last_synced=datetime.now(timezone.utc)
        )
        session.add(acc)
        await session.commit()
        await session.refresh(acc)
        account_id = acc.id

    # Get transactions (should trigger sync)
    response = await async_client.get(f"/accounts/{account_id}/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["account_id"] == account_id

    # Verify transaction added to DB
    async with TestingSessionLocal() as session:
        txs = await session.get(Transaction, data[0]["id"])
        assert txs is not None

@pytest.mark.asyncio
async def test_get_balance(async_client):
     async with TestingSessionLocal() as session:
        conn = BankConnection(
            user_id="user_bal",
            bank_name="Bal Bank",
            access_token="token",
            status=ConnectionStatus.ACTIVE
        )
        session.add(conn)
        await session.commit()
        await session.refresh(conn)

        acc = BankAccount(
            connection_id=conn.id,
            account_number_hash="hash",
            account_type="checking",
            balance=1234.56,
            currency="USD"
        )
        session.add(acc)
        await session.commit()
        account_id = acc.id

     response = await async_client.get(f"/accounts/{account_id}/balance")
     assert response.status_code == 200
     data = response.json()
     assert float(data["balance"]) == 1234.56
