import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.main import app
from src.core.database import Base, get_db
from src.models.secondary_market import ListingStatus, TransferType

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_listing(client):
    response = await client.post("/api/v1/listings/create", json={
        "ticket_id": "TICKET123",
        "seller_id": "USER1",
        "asking_price": 100.0,
        "platform_fee_pct": 0.1
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ticket_id"] == "TICKET123"
    assert data["status"] == "listed"

@pytest.mark.asyncio
async def test_get_listings(client):
    # Create a listing first
    await client.post("/api/v1/listings/create", json={
        "ticket_id": "TICKET123",
        "seller_id": "USER1",
        "asking_price": 100.0,
        "platform_fee_pct": 0.1
    })

    response = await client.get("/api/v1/listings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["ticket_id"] == "TICKET123"

@pytest.mark.asyncio
async def test_purchase_listing(client):
    # Create listing
    create_res = await client.post("/api/v1/listings/create", json={
        "ticket_id": "TICKET123",
        "seller_id": "USER1",
        "asking_price": 100.0,
        "platform_fee_pct": 0.1
    })
    listing_id = create_res.json()["id"]

    # Purchase
    response = await client.post(f"/api/v1/listings/{listing_id}/purchase", json={
        "buyer_id": "USER2"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True

    # Verify status changed (this requires checking listing again)
    listings_res = await client.get("/api/v1/listings")
    listings = listings_res.json()
    # Should be empty or filtered out if we filter by status=listed
    assert len(listings) == 0

@pytest.mark.asyncio
async def test_transfer_ticket(client):
    response = await client.post("/api/v1/tickets/TICKET123/transfer", json={
        "from_user": "USER1",
        "to_user": "USER2",
        "transfer_type": "gift",
        "transfer_price": 0.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == "TICKET123"
    assert data["transfer_type"] == "gift"

@pytest.mark.asyncio
async def test_join_waitlist(client):
    response = await client.get("/api/v1/waitlist/EVENT1/join", params={
        "user_id": "USER1",
        "tier_preference": "VIP",
        "max_price": 200.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Joined waitlist"

@pytest.mark.asyncio
async def test_waitlist_position(client):
    # Join waitlist user 1
    await client.get("/api/v1/waitlist/EVENT1/join", params={
        "user_id": "USER1",
        "tier_preference": "VIP",
        "max_price": 200.0
    })
    # Join waitlist user 2
    await client.get("/api/v1/waitlist/EVENT1/join", params={
        "user_id": "USER2",
        "tier_preference": "VIP",
        "max_price": 200.0
    })

    response = await client.get("/api/v1/waitlist/EVENT1/position", params={"user_id": "USER2"})
    assert response.status_code == 200
    data = response.json()
    assert data["position"] == 2
