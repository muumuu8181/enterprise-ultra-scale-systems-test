import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from src.models.ml_models import Base, MLModel, DeployedModel, ABTest
from src.services.model_registry import ModelRegistryService

# Test DB Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    """
    Creates a fresh in-memory database for each test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_register_model(db_session):
    """Test registering a new model"""
    service = ModelRegistryService(db_session)
    model = await service.register_model(
        name="TestModel",
        version="1.0",
        framework="PyTorch",
        artifact_uri="s3://test/model.pth",
        metrics={"accuracy": 0.95}
    )
    assert model.id is not None
    assert model.name == "TestModel"
    assert model.metrics["accuracy"] == 0.95
    assert model.status == "registered"

@pytest.mark.asyncio
async def test_get_model(db_session):
    """Test retrieving a model by ID"""
    service = ModelRegistryService(db_session)
    # Pre-register
    model = await service.register_model("M1", "v1", "TF", "uri")

    fetched = await service.get_model(model.id)
    assert fetched is not None
    assert fetched.name == "M1"
    assert fetched.id == model.id

@pytest.mark.asyncio
async def test_list_models(db_session):
    """Test listing models"""
    service = ModelRegistryService(db_session)
    await service.register_model("M1", "v1", "TF", "uri1")
    await service.register_model("M2", "v2", "TF", "uri2")

    models = await service.list_models()
    assert len(models) == 2
    assert models[0].name == "M1"
    assert models[1].name == "M2"

@pytest.mark.asyncio
async def test_deploy_model(db_session):
    """Test deploying a model"""
    service = ModelRegistryService(db_session)
    model = await service.register_model("M1", "v1", "TF", "uri")

    deployment = await service.deploy_model(
        model_id=model.id,
        endpoint_url="http://api.model.com",
        traffic_split=50
    )

    assert deployment.id is not None
    assert deployment.endpoint_url == "http://api.model.com"
    assert deployment.traffic_split == 50

    # Check model status updated
    updated_model = await service.get_model(model.id)
    assert updated_model.status == "deployed"

@pytest.mark.asyncio
async def test_archive_model(db_session):
    """Test archiving a model"""
    service = ModelRegistryService(db_session)
    model = await service.register_model("M1", "v1", "TF", "uri")

    archived = await service.archive_model(model.id)
    assert archived.status == "archived"

@pytest.mark.asyncio
async def test_create_ab_test_logic(db_session):
    """Test AB Test creation logic (simulating API logic)"""
    service = ModelRegistryService(db_session)
    m1 = await service.register_model("M1", "v1", "TF", "uri")
    m2 = await service.register_model("M2", "v1", "TF", "uri")

    ab_test = ABTest(
        name="TestAB",
        model_a_id=m1.id,
        model_b_id=m2.id,
        traffic_ratio=0.5,
        status="scheduled"
    )
    db_session.add(ab_test)
    await db_session.commit()

    result = await db_session.execute(select(ABTest).where(ABTest.name == "TestAB"))
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.traffic_ratio == 0.5
    assert fetched.model_a_id == m1.id
