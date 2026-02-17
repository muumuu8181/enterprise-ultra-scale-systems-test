import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, Depends
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator

from src.models.ml_models import Base
from src.services.model_registry import get_db
from src.api.v1.llm import router, get_gateway
from src.services.llm_gateway import LLMGateway

# Test DB Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    # Mock specific redis methods used
    mock.incr.return_value = 1
    mock.get.return_value = None
    return mock

@pytest_asyncio.fixture
async def client(db_session, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Override get_gateway to return a gateway with mock redis
    # Since get_gateway normally takes (db), we can override it with a function that takes nothing
    # (or whatever FastAPI injects, but here we hardcode the return)
    # However, since LLMGateway needs db_session for log_usage, we should pass it.

    def override_get_gateway():
        return LLMGateway(db_session, redis=mock_redis)

    app.dependency_overrides[get_gateway] = override_get_gateway

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_completion(client, mock_redis):
    payload = {
        "model": "gpt-4",
        "prompt": "Hello world",
        "max_tokens": 50,
        "temperature": 0.5
    }
    response = await client.post("/llm/completions", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["model"] == "gpt-4"
    assert "choices" in data

    # Verify Redis usage
    mock_redis.incr.assert_called() # Rate limit
    mock_redis.set.assert_called() # Cache

@pytest.mark.asyncio
async def test_rate_limit_exceeded(client, mock_redis):
    # Mock redis to return limit exceeded
    mock_redis.incr.return_value = 100 # limit is 60

    payload = {
        "model": "gpt-4",
        "prompt": "Hello",
    }
    response = await client.post("/llm/completions", json=payload)
    assert response.status_code == 429

@pytest.mark.asyncio
async def test_chat_completion(client):
    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hi"}],
        "system_prompt": "You are a bot"
    }
    response = await client.post("/llm/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data

@pytest.mark.asyncio
async def test_embeddings(client):
    payload = {
        "model": "text-embedding-ada-002",
        "text": "Hello world"
    }
    response = await client.post("/llm/embeddings", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert data["data"][0]["object"] == "embedding"

@pytest.mark.asyncio
async def test_fine_tune_jobs(client):
    payload = {
        "base_model": "gpt-3.5-turbo",
        "training_file_id": "file-123"
    }
    response = await client.post("/llm/fine-tune/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    job_id = data["id"]

    response_get = await client.get(f"/llm/fine-tune/jobs/{job_id}")
    assert response_get.status_code == 200
    assert response_get.json()["id"] == job_id
