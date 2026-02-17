import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.model_registry import ModelRegistryService
from src.models.ml_models import MLModel, DeployedModel, ABTest
from sqlalchemy import select

# Helper to mock redis in all tests
@pytest.fixture
def mock_redis_client():
    with patch("src.services.model_registry.redis_client", new_callable=AsyncMock) as mock:
        yield mock

@pytest.mark.asyncio
async def test_register_model_success(db_session, mock_redis_client):
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True

    service = ModelRegistryService(db_session)

    model = await service.register_model(
        name="test_model",
        version="1.0",
        framework="pytorch",
        artifact_uri="s3://bucket/model",
        metrics={"accuracy": 0.95}
    )

    assert model.id is not None
    assert model.name == "test_model"
    assert model.status == "registered"

@pytest.mark.asyncio
async def test_register_duplicate_version_fails(db_session, mock_redis_client):
    service = ModelRegistryService(db_session)
    await service.register_model("model1", "v1", "fw", "uri", {})

    with pytest.raises(ValueError, match="already exists"):
        await service.register_model("model1", "v1", "fw", "uri", {})

@pytest.mark.asyncio
async def test_deploy_model_changes_status(db_session, mock_redis_client):
    mock_redis_client.get.return_value = None
    mock_redis_client.delete.return_value = True

    service = ModelRegistryService(db_session)
    model = await service.register_model("model_deploy", "v1", "fw", "uri", {})

    deployment = await service.deploy_model(model.id, "http://endpoint", 100)

    assert deployment.status == "deployed"

    stmt = select(MLModel).where(MLModel.id == model.id)
    res = await db_session.execute(stmt)
    updated_model = res.scalar_one()
    assert updated_model.status == "deployed"

@pytest.mark.asyncio
async def test_ab_test_traffic_split(db_session, mock_redis_client):
    mock_redis_client.get.return_value = None

    service = ModelRegistryService(db_session)

    m1 = await service.register_model("m1", "v1", "fw", "uri", {})
    m2 = await service.register_model("m2", "v1", "fw", "uri", {})

    test = await service.create_ab_test("ab_test_1", m1.id, m2.id, 0.5)

    assert test.traffic_ratio == 0.5
    assert test.status == "active"
    assert test.model_a_id == m1.id
    assert test.model_b_id == m2.id

@pytest.mark.asyncio
async def test_list_models_with_filters(db_session, mock_redis_client):
    service = ModelRegistryService(db_session)

    await service.register_model("m1", "v1", "pytorch", "uri", {})
    await service.register_model("m2", "v1", "sklearn", "uri", {})
    await service.register_model("m3", "v2", "pytorch", "uri", {})

    models = await service.list_models(framework="pytorch")
    assert len(models) == 2

    models_sklearn = await service.list_models(framework="sklearn")
    assert len(models_sklearn) == 1
