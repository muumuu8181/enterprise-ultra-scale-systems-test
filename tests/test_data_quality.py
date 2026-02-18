import pytest
import os
import sys
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Set TESTING env var
os.environ["TESTING"] = "1"

from src.main import app
from src.api.v1.data_quality import get_db
from src.models.base import Base
from src.models.dq_models import DQRule, DQReport

# Use file-based DB for robustness in mixed sync/async test environment
TEST_DB_FILE = "./test_dq.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
SYNC_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

# Async engine for the app
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def prepare_db_sync():
    # Setup
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    sync_engine = create_engine(SYNC_DATABASE_URL)
    Base.metadata.create_all(sync_engine)

    yield

    # Teardown
    sync_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

@pytest.mark.asyncio
async def test_create_rule():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/dq/rules",
            json={
                "dataset_id": "ds_test_1",
                "rule_type": "null_check",
                "condition": {"column": "age", "threshold": 0.1},
                "severity": "warning"
            }
        )
    assert response.status_code == 201
    data = response.json()
    assert data["dataset_id"] == "ds_test_1"
    assert "id" in data

@pytest.mark.asyncio
async def test_validate_dataset():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/dq/validate/ds_test_1")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "ds_test_1"
    assert "overall_score" in data
    assert "issues" in data
    assert data["overall_score"] < 100

@pytest.mark.asyncio
async def test_get_reports():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/dq/validate/ds_test_1")
        response = await ac.get("/dq/reports/ds_test_1")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["dataset_id"] == "ds_test_1"
