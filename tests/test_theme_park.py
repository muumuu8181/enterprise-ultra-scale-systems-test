import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db

# Use in-memory SQLite for testing
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

@pytest_asyncio.fixture(scope="module")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_attraction(init_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/attractions", json={
            "name": "Space Mountain",
            "park_zone": "Tomorrowland",
            "ride_type": "coaster",
            "capacity_per_hour": 1500,
            "height_requirement_cm": 120,
            "duration_min": 3,
            "status": "operating"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Space Mountain"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_attractions(init_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/attractions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Space Mountain"

@pytest.mark.asyncio
async def test_purchase_ticket(init_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/tickets/purchase", json={
            "guest_id": "guest_123",
            "ticket_type": "single_day",
            "zones_access": ["Tomorrowland", "Fantasyland"]
        })
    assert response.status_code == 200
    data = response.json()
    assert data["guest_id"] == "guest_123"
    assert data["status"] == "active"
