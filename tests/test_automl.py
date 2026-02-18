import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
import asyncio
import os
from src.main import app
from src.database import engine
from src.models.ml_models import Base

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_automl_service():
    with patch("src.api.v1.automl.AutoMLService") as MockService:
        instance = MockService.return_value
        instance.load_data.return_value = None
        instance.select_best_algorithm.return_value = ("xgboost", {"n_estimators": 100}, 0.95)
        instance.generate_model_report.return_value = {"metrics": {"accuracy": 0.95}}
        instance.export_to_onnx.side_effect = lambda path: open(path, 'w').close() # Create empty file
        yield MockService

@pytest.mark.asyncio
async def test_automl_flow(mock_automl_service):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Start Job
        response = await ac.post("/api/v1/automl/start", json={
            "dataset_id": "mock",
            "target_column": "target",
            "metric": "accuracy"
        })
        assert response.status_code == 200, response.text
        data = response.json()
        job_id = data["id"]
        assert job_id is not None
        assert data["status"] == "PENDING"

        # 2. Poll Status
        # Wait for background task to complete
        status = "PENDING"
        for _ in range(20):
            response = await ac.get(f"/api/v1/automl/{job_id}/status")
            status = response.json()["status"]
            if status in ["COMPLETED", "FAILED"]:
                break
            await asyncio.sleep(0.1)

        if status == "FAILED":
            print(f"Job Failed: {response.json().get('error_message')}")

        assert status == "COMPLETED"

        # 3. Get Results
        response = await ac.get(f"/api/v1/automl/{job_id}/results")
        assert response.status_code == 200
        results = response.json()
        # Report structure: metrics -> metrics -> accuracy
        assert results["metrics"]["metrics"]["accuracy"] == 0.95
        assert results["best_algorithm"] == "xgboost"

        # 4. Promote
        response = await ac.post(f"/api/v1/automl/{job_id}/promote", json={
            "model_name": "test-model",
            "description": "Best model ever"
        })
        assert response.status_code == 200
        promote_data = response.json()
        assert promote_data["version"] >= 1
        assert promote_data["status"] == "STAGING"

@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    yield
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    if os.path.exists("artifacts"):
        import shutil
        shutil.rmtree("artifacts")
