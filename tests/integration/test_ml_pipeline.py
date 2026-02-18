import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from src.models.ml_models import MLModel, DeployedModel, Experiment, Run, ABTest
from src.services.model_registry import ModelRegistryService
from src.services.inference_engine import InferenceEngine
from tests.fixtures.sample_models import sample_linear_regression_model

# Fixtures from conftest.py are automatically available

@pytest.mark.asyncio
async def test_register_and_deploy_model(db_session, sample_linear_regression_model):
    registry_service = ModelRegistryService(db_session)

    # Register
    model = await registry_service.register_model(
        name="LinearReg",
        version="1.0",
        framework="sklearn",
        artifact_uri=sample_linear_regression_model,
        metrics={"r2": 0.9}
    )
    assert model.id is not None
    assert model.status == "registered"

    # Deploy
    deployment = await registry_service.deploy_model(
        model_id=model.id,
        endpoint_url="http://ml-platform/predict/linear-reg",
        traffic_split=100
    )

    assert deployment.id is not None
    assert deployment.status == "active"

    # Verify model status update
    updated_model = await registry_service.get_model(model.id)
    assert updated_model.status == "deployed"

@pytest.mark.asyncio
async def test_ab_test_routing(db_session, redis_client):
    registry_service = ModelRegistryService(db_session)
    inference_engine = InferenceEngine(db_session, redis_client)

    # Register two models
    m1 = await registry_service.register_model("ModelA", "v1", "sklearn", "uri1")
    m2 = await registry_service.register_model("ModelB", "v1", "sklearn", "uri2")

    # Create AB Test
    ab_test = ABTest(
        name="TestAB",
        model_a_id=m1.id,
        model_b_id=m2.id,
        traffic_ratio=0.5,
        status="running"
    )
    db_session.add(ab_test)
    await db_session.commit()
    await db_session.refresh(ab_test)

    # Test routing for different users
    results = {"m1": 0, "m2": 0}
    for i in range(100):
        model_id = await inference_engine.route_ab_test(ab_test.id, f"user_{i}")
        if model_id == m1.id:
            results["m1"] += 1
        else:
            results["m2"] += 1

    # Check distribution (approx 50/50, allow variance)
    # With 100 samples, variance can be high, but usually > 30 each side is safe enough
    assert results["m1"] > 30
    assert results["m2"] > 30

    # Test sticky session
    user_id = "sticky_user"
    first_route = await inference_engine.route_ab_test(ab_test.id, user_id)
    for _ in range(5):
        route = await inference_engine.route_ab_test(ab_test.id, user_id)
        assert route == first_route

@pytest.mark.asyncio
async def test_experiment_tracking_full_flow(db_session):
    # Create Experiment
    experiment = Experiment(name="NewExp", description="Test Experiment")
    db_session.add(experiment)
    await db_session.commit()
    await db_session.refresh(experiment)

    assert experiment.id is not None

    # Create Run
    run = Run(
        experiment_id=experiment.id,
        status="running",
        params={"learning_rate": 0.01},
        start_time=datetime.now(timezone.utc)
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    assert run.id is not None
    assert run.experiment_id == experiment.id

    # Update Run with metrics and complete
    run.metrics = {"accuracy": 0.95}
    run.status = "completed"
    run.end_time = datetime.now(timezone.utc)
    db_session.add(run)
    await db_session.commit()

    # Verify
    stmt = select(Run).where(Run.id == run.id)
    result = await db_session.execute(stmt)
    fetched_run = result.scalars().first()

    assert fetched_run.status == "completed"
    assert fetched_run.metrics["accuracy"] == 0.95

@pytest.mark.asyncio
async def test_batch_prediction(db_session, redis_client):
    registry_service = ModelRegistryService(db_session)
    inference_engine = InferenceEngine(db_session, redis_client)

    # Register Model
    model = await registry_service.register_model("BatchModel", "v1", "sklearn", "uri")

    # Prepare batch input
    inputs = [{"feature1": i} for i in range(10)]

    # Run batch prediction
    results = await inference_engine.batch_predict(model.id, inputs)

    assert len(results) == 10
    for res in results:
        assert res["model_id"] == model.id
        assert "prediction" in res
