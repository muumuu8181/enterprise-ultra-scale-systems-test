import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.database import Base, get_db
from src.main import app
from src.models.warehouse_models import StorageLocation

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

import pytest_asyncio

@pytest_asyncio.fixture
async def client():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_generate_pick_list(client):
    response = await client.post("/api/v1/pick-lists/generate", json={"order_id": "ORD-123"})
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "ORD-123"
    assert "id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_inventory_update(client):
    # Manually seed a location
    async with TestingSessionLocal() as db:
        loc = StorageLocation(
            zone_id="Z1", aisle="A1", rack="R1", level="L1", bin="B1", sku="SKU-TEST", quantity=10
        )
        db.add(loc)
        await db.commit()
        await db.refresh(loc)
        loc_id = loc.id

    response = await client.post(f"/api/v1/locations/{loc_id}/inventory-update", json={"quantity_change": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["new_quantity"] == 15

@pytest.mark.asyncio
async def test_trigger_replenishment(client):
    response = await client.post("/api/v1/replenishment/trigger", json={
        "sku": "SKU-REP",
        "from_zone": "Z1",
        "to_zone": "Z2",
        "quantity": 50,
        "triggered_by": "min_stock"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["sku"] == "SKU-REP"
    assert data["quantity"] == 50

@pytest.mark.asyncio
async def test_get_heatmap(client):
    response = await client.get("/api/v1/locations/heatmap")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
