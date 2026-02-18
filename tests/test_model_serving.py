import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from src.main import app
from src.core.model_cache import ModelCache
from src.services.model_server import model_server
from src.models.ml_models import MLModel

client = TestClient(app)

# Unit Test for ModelCache
def test_model_cache_lru():
    cache = ModelCache(capacity=2)
    cache.put(1, "model1")
    cache.put(2, "model2")
    assert cache.get(1) == "model1"

    # Access 1 to make it recently used
    cache.get(1)

    cache.put(3, "model3") # Should evict 2 (LRU)
    assert cache.get(2) is None
    assert cache.get(1) == "model1"
    assert cache.get(3) == "model3"

def test_model_cache_memory_usage():
    cache = ModelCache()
    cache.put(1, "a" * 1000)
    usage = cache.get_memory_usage()
    assert usage > 0

# API Tests
@pytest.mark.asyncio
async def test_load_model_endpoint():
    # Mock DB dependency
    mock_session = AsyncMock()
    # Mock result for select(MLModel)
    mock_result = MagicMock()
    mock_model = MLModel(id=1, name="test_model", artifact_uri="s3://test", version="1.0", framework="pytorch")
    mock_result.scalar_one_or_none.return_value = mock_model
    mock_session.execute.return_value = mock_result

    # Override get_db
    async def override_get_db():
        yield mock_session

    from src.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Call API
    response = client.post("/serving/models/1/load")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify ModelServer state
    assert model_server.health_check(1) is True

    # Test Health Endpoint
    response = client.get("/serving/models/1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Cleanup
    model_server.unload_model(1)

    # Verify unload
    response = client.get("/serving/models/1/health")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_load_model_not_found():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    async def override_get_db():
        yield mock_session

    from src.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    response = client.post("/serving/models/999/load")
    assert response.status_code == 404

def test_predict_async():
    # Test submission
    with patch("src.services.model_server.predict_async_task.delay") as mock_delay:
        mock_delay.return_value.id = "test_job_id"
        response = client.post("/serving/predict/async", json={"model_id": 1, "input_data": {"foo": "bar"}})
        assert response.status_code == 200
        assert response.json()["job_id"] == "test_job_id"

    # Test retrieval
    with patch("src.api.v1.model_serving.AsyncResult") as MockAsyncResult:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"prediction": "async_dummy_result"}
        MockAsyncResult.return_value = mock_result

        response = client.get("/serving/predict/test_job_id/result")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["result"]["prediction"] == "async_dummy_result"
