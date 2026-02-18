import pytest
import asyncio
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from fastapi.testclient import TestClient
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.models.robot_models import Base, Robot, RobotTask, RobotStatus, RobotType, TaskType, WarehouseZone, ZoneType
from src.api.v1.robots import router, get_db
from src.services.fleet_manager import dispatch_task

# Setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session

app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def db_session():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_fleet_status(db_session):
    # Seed data
    robot = Robot(serial="R001", robot_type=RobotType.PICKER, status=RobotStatus.IDLE, battery_pct=100.0)
    db_session.add(robot)
    await db_session.commit()

    # We use TestClient but we need to ensure the app uses the same loop/db?
    # With TestClient, it starts the app.
    # But since we override dependency to use AsyncSessionLocal which uses `engine` bound to the loop?
    # SQLAlchemy async engine is bound to the loop it was created in?
    # If TestClient runs in a different thread/loop, it might crash.
    # To be safe, let's just test service logic and API endpoints directly (calling the function)
    # OR use httpx.AsyncClient.

    # Let's try calling the endpoint function directly for simplicity and robustness in this env
    # without worrying about HTTP client overhead, if possible.
    # But TestClient is better integration test.

    with TestClient(app) as client:
        response = client.get("/robots/fleet/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["serial"] == "R001"

@pytest.mark.asyncio
async def test_dispatch_logic(db_session):
    # Seed
    robot = Robot(serial="R002", robot_type=RobotType.PICKER, status=RobotStatus.IDLE, battery_pct=80.0)
    db_session.add(robot)
    await db_session.commit()

    task = RobotTask(task_type=TaskType.PICK, priority=1, payload={"item": "A1"})

    # Call service directly
    result = await dispatch_task(db_session, task)
    assert result is not None
    assert result.id == robot.id
    assert result.status == RobotStatus.WORKING
    assert result.current_task_id is not None
    assert result.current_task_id == task.id

@pytest.mark.asyncio
async def test_api_assign_task(db_session):
    robot = Robot(serial="R003", robot_type=RobotType.CARRIER, status=RobotStatus.IDLE, battery_pct=90.0)
    db_session.add(robot)
    await db_session.commit()

    with TestClient(app) as client:
        response = client.post(f"/robots/{robot.id}/assign-task", json={
            "task_type": "carry",
            "priority": 2,
            "payload": {"target": "ZoneB"}
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "working"

    # Check DB
    await db_session.refresh(robot)
    assert robot.status == RobotStatus.WORKING

@pytest.mark.asyncio
async def test_optimize_dispatch(db_session):
    r1 = Robot(serial="R004", robot_type=RobotType.PICKER, status=RobotStatus.IDLE, battery_pct=100.0)
    r2 = Robot(serial="R005", robot_type=RobotType.CARRIER, status=RobotStatus.IDLE, battery_pct=100.0)
    db_session.add_all([r1, r2])
    await db_session.commit()

    tasks = [
        {"task_type": "pick", "priority": 1, "payload": {}},
        {"task_type": "carry", "priority": 1, "payload": {}}
    ]

    with TestClient(app) as client:
        response = client.post("/tasks/optimize-dispatch", json=tasks)

        assert response.status_code == 200
        assignments = response.json()
        assert len(assignments) == 2

        # Verify mapping (pick -> picker, carry -> carrier)
        task_ids = [a["task_id"] for a in assignments]
        robot_ids = [a["robot_id"] for a in assignments]

        assert r1.id in robot_ids
        assert r2.id in robot_ids
