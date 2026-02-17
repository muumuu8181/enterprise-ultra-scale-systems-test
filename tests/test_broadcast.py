import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.main import app
from src.database import get_db, Base
from src.models.broadcast_models import ChannelType, ChannelStatus, ProgramStatus

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_channel(client):
    response = await client.post(
        "/api/v1/broadcast/channels/create",
        json={
            "name": "Test Channel",
            "channel_type": "tv",
            "frequency": "101.5",
            "region": "US"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Channel"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_channels(client):
    await client.post(
        "/api/v1/broadcast/channels/create",
        json={"name": "Channel 1", "channel_type": "tv"}
    )
    response = await client.get("/api/v1/broadcast/channels")
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_schedule_program(client):
    # Create channel first
    channel_resp = await client.post(
        "/api/v1/broadcast/channels/create",
        json={"name": "Channel 1", "channel_type": "tv"}
    )
    channel = channel_resp.json()

    response = await client.post(
        "/api/v1/broadcast/programs/schedule",
        json={
            "title": "Morning Show",
            "channel_id": channel["id"],
            "duration_min": 60,
            "scheduled_at": "2023-10-27T08:00:00",
            "status": "scheduled"
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Morning Show"

@pytest.mark.asyncio
async def test_book_adslot(client):
    # Setup: Create channel, program
    channel = (await client.post(
        "/api/v1/broadcast/channels/create",
        json={"name": "Channel 1", "channel_type": "tv"}
    )).json()

    program = (await client.post(
        "/api/v1/broadcast/programs/schedule",
        json={
            "title": "Show 1",
            "channel_id": channel["id"],
            "duration_min": 60,
            "scheduled_at": "2023-10-27T08:00:00"
        }
    )).json()

    # Create adslot
    adslot = (await client.post(
        "/api/v1/broadcast/adslots/create",
        json={
            "program_id": program["id"],
            "position": "pre",
            "duration_sec": 30,
            "price": 100.0
        }
    )).json()

    # Book adslot
    response = await client.post(
        "/api/v1/broadcast/adslots/book",
        json={
            "adslot_id": adslot["id"],
            "advertiser_id": 123,
            "creative_url": "http://example.com/ad.mp4"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "booked"

@pytest.mark.asyncio
async def test_get_schedule(client):
    # Setup
    channel = (await client.post(
        "/api/v1/broadcast/channels/create",
        json={"name": "Channel 1", "channel_type": "tv"}
    )).json()

    await client.post(
        "/api/v1/broadcast/programs/schedule",
        json={
            "title": "Morning Show",
            "channel_id": channel["id"],
            "duration_min": 60,
            "scheduled_at": "2023-10-27T08:00:00",
            "status": "scheduled"
        }
    )

    # Test
    response = await client.get(f"/api/v1/broadcast/schedule/{channel['id']}?date=2023-10-27")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Morning Show"
