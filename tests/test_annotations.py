import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import Base and models to ensure they are registered in metadata
from src.models.ml_models import Base
# Importing main ensures annotation models are imported via src.main -> src.models.annotation_models
from src.main import app
from src.services.model_registry import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_task(client):
    response = await client.post("/api/v1/annotations/tasks", json={
        "dataset_id": 101,
        "task_type": "classification"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == 101
    assert data["task_type"] == "classification"
    assert data["status"] == "pending"
    assert data["total_items"] == 10
    assert data["completed_items"] == 0

@pytest.mark.asyncio
async def test_get_task_items(client):
    # Create task first
    create_res = await client.post("/api/v1/annotations/tasks", json={
        "dataset_id": 102,
        "task_type": "detection"
    })
    task_id = create_res.json()["id"]

    # Get items
    response = await client.get(f"/api/v1/annotations/tasks/{task_id}/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 10
    assert items[0]["task_id"] == task_id
    assert items[0]["status"] == "pending"

@pytest.mark.asyncio
async def test_annotate_item(client):
    # Create task
    create_res = await client.post("/api/v1/annotations/tasks", json={
        "dataset_id": 103,
        "task_type": "segmentation"
    })
    task_id = create_res.json()["id"]

    # Get an item
    items_res = await client.get(f"/api/v1/annotations/tasks/{task_id}/items")
    item_id = items_res.json()[0]["id"]

    # Annotate item
    response = await client.post(f"/api/v1/annotations/items/{item_id}/annotate", json={
        "label": {"class": "cat", "bbox": [10, 10, 100, 100]},
        "confidence": 0.95,
        "annotator_id": "user_123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == item_id
    assert data["annotator_id"] == "user_123"

    # Verify task progress updated
    progress_res = await client.get(f"/api/v1/annotations/tasks/{task_id}/progress")
    progress = progress_res.json()
    assert progress["completed_items"] == 1
    assert progress["progress_percentage"] == 10.0

@pytest.mark.asyncio
async def test_export_annotations(client):
    # Create task & Annotate one item
    create_res = await client.post("/api/v1/annotations/tasks", json={
        "dataset_id": 104,
        "task_type": "detection"
    })
    task_id = create_res.json()["id"]
    items_res = await client.get(f"/api/v1/annotations/tasks/{task_id}/items")
    item_id = items_res.json()[0]["id"]

    await client.post(f"/api/v1/annotations/items/{item_id}/annotate", json={
        "label": {"class": "dog"},
        "confidence": 0.88,
        "annotator_id": "user_123"
    })

    # Export
    response = await client.post(f"/api/v1/annotations/tasks/{task_id}/export?format=coco")
    assert response.status_code == 200
    data = response.json()
    assert "images" in data
    assert "annotations" in data
    assert len(data["annotations"]) == 1
    assert data["annotations"][0]["score"] == 0.88
