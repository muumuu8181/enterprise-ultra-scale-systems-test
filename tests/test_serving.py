import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.main import app
from src.core.database import Base, get_db
from src.models.serving_models import InferenceEndpoint

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_deploy_endpoint(client):
    response = await client.post("/api/v1/serving/endpoints/deploy", json={
        "model_id": "model-v1",
        "endpoint_url": "http://model-service:8080/predict",
        "auth_type": "api_key"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "model-v1"
    assert "id" in data
    return data["id"]

@pytest.mark.asyncio
async def test_predict(client):
    # Deploy first
    deploy_response = await client.post("/api/v1/serving/endpoints/deploy", json={
        "model_id": "model-v2",
        "endpoint_url": "http://model-service-v2:8080/predict",
        "auth_type": "api_key"
    })
    endpoint_id = deploy_response.json()["id"]

    # Predict
    response = await client.post(f"/api/v1/serving/endpoints/{endpoint_id}/predict", json={
        "input_data": {"feature1": 0.5, "feature2": 0.1}
    })
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "latency_ms" in data

@pytest.mark.asyncio
async def test_get_metrics(client):
    # Deploy first
    deploy_response = await client.post("/api/v1/serving/endpoints/deploy", json={
        "model_id": "model-v3",
        "endpoint_url": "http://model-service-v3:8080/predict",
        "auth_type": "api_key"
    })
    endpoint_id = deploy_response.json()["id"]

    response = await client.get(f"/api/v1/serving/endpoints/{endpoint_id}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "latency_p99_ms" in data

@pytest.mark.asyncio
async def test_monitoring_alerts(client):
    response = await client.post("/api/v1/serving/monitoring/alerts", json={
        "endpoint_id": 1,
        "metric": "error_rate",
        "threshold": 0.05
    })
    assert response.status_code == 200
    assert response.json()["alert_configured"] is True

@pytest.mark.asyncio
async def test_ab_test(client):
    # Deploy first
    deploy_response = await client.post("/api/v1/serving/endpoints/deploy", json={
        "model_id": "model-ab",
        "endpoint_url": "http://model-service-ab:8080/predict",
        "auth_type": "api_key"
    })
    endpoint_id = deploy_response.json()["id"]

    response = await client.post(f"/api/v1/serving/endpoints/{endpoint_id}/ab-test", json={
        "variant_b_url": "http://model-service-ab-b:8080/predict",
        "traffic_split": 0.5
    })
    assert response.status_code == 200
    assert response.json()["status"] == "started"
