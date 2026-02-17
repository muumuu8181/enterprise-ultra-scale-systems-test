import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
from decimal import Decimal

from src.main import app
from src.models.base import Base
from src.models.fx_models import FXRate, FXOrder, OrderType, OrderStatus
from src.api.dependencies import get_db
from src.services.fx_service import FXService

# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
async def test_get_rates(async_client, setup_db):
    # Seed data
    async with TestingSessionLocal() as session:
        rate = FXRate(
            base_currency="USD",
            quote_currency="JPY",
            bid=Decimal("150.00"),
            ask=Decimal("150.10"),
            mid=Decimal("150.05"),
            timestamp=datetime.now(timezone.utc)
        )
        session.add(rate)
        await session.commit()

    response = await async_client.get("/fx/rates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["base_currency"] == "USD"
    assert data[0]["quote_currency"] == "JPY"
    assert data[0]["bid"] == "150.00000000"

@pytest.mark.asyncio
async def test_convert_currency(async_client, setup_db):
    async with TestingSessionLocal() as session:
        rate = FXRate(
            base_currency="USD",
            quote_currency="JPY",
            bid=Decimal("150.00"),
            ask=Decimal("150.10"),
            mid=Decimal("150.05")
        )
        session.add(rate)
        await session.commit()

    payload = {
        "from_currency": "USD",
        "to_currency": "JPY",
        "amount": 100
    }
    response = await async_client.post("/fx/convert", json=payload)
    assert response.status_code == 200
    data = response.json()
    # 100 * 150.00 = 15000.00
    assert float(data["converted_amount"]) == 15000.0

@pytest.mark.asyncio
async def test_place_market_order(async_client, setup_db):
    async with TestingSessionLocal() as session:
        rate = FXRate(
            base_currency="USD",
            quote_currency="JPY",
            bid=Decimal("150.00"),
            ask=Decimal("150.10"),
            mid=Decimal("150.05")
        )
        session.add(rate)
        await session.commit()

    payload = {
        "customer_id": "cust_123",
        "from_currency": "USD",
        "to_currency": "JPY",
        "amount": 100,
        "order_type": "MARKET"
    }
    response = await async_client.post("/fx/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FILLED"
    assert float(data["executed_rate"]) == 150.0

@pytest.mark.asyncio
async def test_place_limit_order_match(async_client, setup_db):
    # Seed rate
    async with TestingSessionLocal() as session:
        rate = FXRate(
            base_currency="USD",
            quote_currency="JPY",
            bid=Decimal("150.00"),
            ask=Decimal("150.10"),
            mid=Decimal("150.05")
        )
        session.add(rate)
        await session.commit()

    # Place Limit Order (Sell USD at >= 149.00) -> Should match immediately because Bid 150.00 >= 149.00
    payload = {
        "customer_id": "cust_limit",
        "from_currency": "USD",
        "to_currency": "JPY",
        "amount": 100,
        "order_type": "LIMIT",
        "limit_rate": 149.00
    }
    response = await async_client.post("/fx/orders", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Check immediate match
    assert data["status"] == "FILLED"
    assert float(data["executed_rate"]) == 150.00

@pytest.mark.asyncio
async def test_place_limit_order_pending(async_client, setup_db):
    # Seed rate
    async with TestingSessionLocal() as session:
        rate = FXRate(
            base_currency="USD",
            quote_currency="JPY",
            bid=Decimal("150.00"),
            ask=Decimal("150.10"),
            mid=Decimal("150.05")
        )
        session.add(rate)
        await session.commit()

    # Place Limit Order (Sell USD at >= 151.00) -> Should NOT match (Bid 150 < 151)
    payload = {
        "customer_id": "cust_limit_pending",
        "from_currency": "USD",
        "to_currency": "JPY",
        "amount": 100,
        "order_type": "LIMIT",
        "limit_rate": 151.00
    }
    response = await async_client.post("/fx/orders", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "PENDING"
    assert data["executed_rate"] is None

@pytest.mark.asyncio
async def test_match_limit_orders_service(setup_db):
    async with TestingSessionLocal() as session:
        # 1. Place Pending Order
        service = FXService(session)
        # Manually create pending order or use place_limit_order with high limit
        # Current rate (if any) or assume none.
        # Let's verify place_limit_order behavior with no rate -> Pending

        order = await service.place_limit_order(
            customer_id="cust_match",
            from_currency="EUR",
            to_currency="USD",
            amount=Decimal("100"),
            limit_rate=Decimal("1.1000")
        )
        assert order.status == OrderStatus.PENDING

        # 2. Add Rate that matches (Bid 1.1050 >= 1.1000)
        rate = FXRate(
            base_currency="EUR",
            quote_currency="USD",
            bid=Decimal("1.1050"),
            ask=Decimal("1.1060"),
            mid=Decimal("1.1055"),
            timestamp=datetime.now(timezone.utc)
        )
        session.add(rate)
        await session.commit()

        # 3. Run Matching
        matched = await service.match_limit_orders()
        assert len(matched) == 1
        assert matched[0].id == order.id
        assert matched[0].status == OrderStatus.FILLED
        assert matched[0].executed_rate == Decimal("1.1050")
