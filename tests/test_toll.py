import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from src.models.toll_models import Base, ETCAccount, TollTransaction
from src.api.v1.toll import router as toll_router
from src.database import get_db

# Create a clean app for testing
app = FastAPI()
app.include_router(toll_router)

# Use SQLite in-memory database
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest_asyncio.fixture
async def db_session():
    # Only create tables relevant to tests to avoid Geometry/Spatialite issues with SQLite
    tables = [ETCAccount.__table__, TollTransaction.__table__]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)

    # Create session
    async with TestingSessionLocal() as session:
        yield session
        # No need to drop tables manually with in-memory db, but good practice
        # await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    # Override get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_record_entry(client):
    response = await client.post("/toll/gates/G01/vehicles/V01/entry")
    assert response.status_code == 200
    assert response.json()["status"] == "entry_recorded"

@pytest.mark.asyncio
async def test_transaction_success(client, db_session):
    # Setup account
    account = ETCAccount(
        vehicle_id="V02",
        balance=5000.0,
        auto_recharge_threshold=1000.0,
        auto_recharge_amount=3000.0
    )
    db_session.add(account)
    await db_session.commit()

    payload = {
        "vehicle_id": "V02",
        "gate_id": "G01",
        "amount": 1500.0,
        "payment_method": "ETC"
    }
    response = await client.post("/toll/transactions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 1500.0

    # Verify balance
    await db_session.refresh(account)
    assert account.balance == 3500.0

@pytest.mark.asyncio
async def test_insufficient_balance(client, db_session):
    account = ETCAccount(
        vehicle_id="V03",
        balance=100.0, # Less than payment
        auto_recharge_threshold=50.0, # Threshold not met (100 > 50)
        auto_recharge_amount=1000.0
    )
    db_session.add(account)
    await db_session.commit()

    payload = {
        "vehicle_id": "V03",
        "gate_id": "G01",
        "amount": 200.0
    }
    response = await client.post("/toll/transactions", json=payload)
    assert response.status_code == 402

@pytest.mark.asyncio
async def test_auto_recharge(client, db_session):
    # Balance 800 < Threshold 1000 -> Should trigger recharge
    account = ETCAccount(
        vehicle_id="V04",
        balance=800.0,
        auto_recharge_threshold=1000.0,
        auto_recharge_amount=2000.0
    )
    db_session.add(account)
    await db_session.commit()

    # Payment 1500.
    # Logic: 800 < 1000 -> Recharge 2000. New balance 2800.
    # 2800 >= 1500 -> Success. New balance 1300.
    payload = {
        "vehicle_id": "V04",
        "gate_id": "G01",
        "amount": 1500.0
    }
    response = await client.post("/toll/transactions", json=payload)
    assert response.status_code == 200

    await db_session.refresh(account)
    # 800 + 2000 - 1500 = 1300
    assert account.balance == 1300.0

@pytest.mark.asyncio
async def test_recharge_api(client, db_session):
    account = ETCAccount(vehicle_id="V05", balance=1000.0)
    db_session.add(account)
    await db_session.commit()

    payload = {"amount": 500.0}
    response = await client.post("/toll/accounts/V05/recharge", json=payload)
    assert response.status_code == 200
    assert response.json()["balance"] == 1500.0

@pytest.mark.asyncio
async def test_history(client, db_session):
    account = ETCAccount(vehicle_id="V06", balance=5000.0)
    db_session.add(account)
    await db_session.commit()

    # Create transaction
    payload = {
        "vehicle_id": "V06",
        "gate_id": "G01",
        "amount": 1000.0
    }
    await client.post("/toll/transactions", json=payload)

    response = await client.get("/toll/history/V06")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["amount"] == 1000.0
