import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.main import app
from src.database import get_db, Base
from src.models.rl_models import TrainingAlgorithm, TrainingTask, Policy, Curriculum
import asyncio

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Fixture to handle async loop
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

import pytest_asyncio
@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_training_task(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/training/tasks/create", json={
            "sim_id": "sim_001",
            "robot_id": "robot_001",
            "objective": {"target": "reach_goal"},
            "algorithm": "ppo",
            "max_episodes": 100
        })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["sim_id"] == "sim_001"
    assert data["algorithm"] == "ppo"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_get_training_progress(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/training/tasks/create", json={
            "sim_id": "sim_002",
            "robot_id": "robot_002",
            "objective": {"target": "lift"},
            "algorithm": "sac",
            "max_episodes": 50
        })
        task_id = create_res.json()["id"]

        response = await ac.get(f"/api/v1/training/tasks/{task_id}/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["current_episode"] == 0

@pytest.mark.asyncio
async def test_evaluate_policy_endpoint(db_session):
    # Insert policy directly
    async with TestingSessionLocal() as session:
        task = TrainingTask(sim_id="s1", robot_id="r1", objective={}, algorithm="td3", max_episodes=10)
        session.add(task)
        await session.commit()
        await session.refresh(task)

        policy = Policy(task_id=task.id, neural_network_config={}, weights_uri="s3://...", checkpoint_episode=10)
        session.add(policy)
        await session.commit()
        await session.refresh(policy)
        policy_id = policy.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/policies/{policy_id}/evaluate?n_episodes=2")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["episodes"] == 2
    assert "mean_reward" in data

@pytest.mark.asyncio
async def test_curriculum_advance(db_session):
    async with TestingSessionLocal() as session:
        curr = Curriculum(name="test_curr", task_sequence=[], auto_advance_threshold=0.5, current_stage=0)
        session.add(curr)
        await session.commit()
        await session.refresh(curr)
        curr_id = curr.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/curriculum/{curr_id}/advance")

    assert response.status_code == 200
    data = response.json()
    assert data["current_stage"] == 1
