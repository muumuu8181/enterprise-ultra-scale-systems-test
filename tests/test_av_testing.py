import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.av_testing_models import Base, TestScenario as ScenarioModel, TestRun as RunModel, SafetyMetric, ScenarioType, MetricType, TestResult
from src.api.v1.av_testing import router

# Setup in-memory database
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def test_models():
    session = SessionLocal()
    scenario = ScenarioModel(
        scenario_type=ScenarioType.highway,
        description="Test highway scenario",
        environment_config={"weather": "sunny"},
        expected_behavior="Drive safely",
        difficulty_level="medium",
        regulatory_standard="ISO 26262"
    )
    session.add(scenario)
    session.commit()
    assert scenario.id is not None

    run = RunModel(
        scenario_id=scenario.id,
        vehicle_id="VIN123",
        result=TestResult.pass_result
    )
    session.add(run)
    session.commit()
    assert run.id is not None
    assert run.result == TestResult.pass_result

    metric = SafetyMetric(
        test_run_id=run.id,
        metric_type=MetricType.ttc,
        value=1.5,
        threshold=2.0,
        passed=True
    )
    session.add(metric)
    session.commit()
    assert metric.id is not None

def test_api():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/scenarios")
    assert response.status_code == 200
    assert response.json() == []

    response = client.post("/scenarios/create", json={
        "scenario_type": "urban",
        "description": "Urban driving",
        "environment_config": {},
        "expected_behavior": "Stop at red light",
        "difficulty_level": "hard",
        "regulatory_standard": "local"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["scenario_type"] == "urban"
