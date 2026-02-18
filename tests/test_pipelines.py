import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.models.ml_models import Base
from src.models.pipeline_models import Pipeline, PipelineRun
from src.services.pipeline_executor import PipelineExecutor

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
async def test_create_pipeline(db_session):
    """Test creating a pipeline directly in DB (simulating API logic)"""
    pipeline = Pipeline(
        name="TestPipeline",
        steps={"step1": "load_data", "step2": "train"},
        schedule_cron="0 0 * * *"
    )
    db_session.add(pipeline)
    await db_session.commit()
    await db_session.refresh(pipeline)

    assert pipeline.id is not None
    assert pipeline.name == "TestPipeline"
    assert pipeline.steps["step1"] == "load_data"

@pytest.mark.asyncio
async def test_execute_pipeline(db_session):
    """Test pipeline execution"""
    # Create Pipeline
    pipeline = Pipeline(name="ExecTest", steps={"step1": "wait"})
    db_session.add(pipeline)
    await db_session.commit()

    # Execute
    executor = PipelineExecutor(db_session)
    run = await executor.execute_pipeline(pipeline.id)

    assert run is not None
    assert run.pipeline_id == pipeline.id
    assert run.status == "completed"
    assert "Execution started" in run.logs
    assert "Step step1 completed" in run.logs

    # Check Pipeline last_run_at
    await db_session.refresh(pipeline)
    assert pipeline.last_run_at is not None

@pytest.mark.asyncio
async def test_pipeline_not_found(db_session):
    """Test execution of non-existent pipeline"""
    executor = PipelineExecutor(db_session)
    run = await executor.execute_pipeline(999)
    assert run is None
