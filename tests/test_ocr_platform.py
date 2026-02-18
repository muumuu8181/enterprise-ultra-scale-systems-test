import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.main import app
from src.database import get_db, Base
from src.models.ocr_models import OCRJob

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_ocr_request(client):
    response = await client.post("/api/v1/items/test-item-1/ocr-request", json={"language": "en"})
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == "test-item-1"
    assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_get_ocr_result(client):
    # Create request first
    create_resp = await client.post("/api/v1/items/test-item-2/ocr-request", json={"language": "fr"})
    job_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/ocr-jobs/{job_id}/result")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["language"] == "fr"

@pytest.mark.asyncio
async def test_batch_enrich(client):
    response = await client.post("/api/v1/items/batch-enrich", json={"item_ids": ["item-1", "item-2"]})
    assert response.status_code == 200
    data = response.json()
    assert len(data["processed_items"]) == 2
