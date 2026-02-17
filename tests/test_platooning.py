import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from src.models.v2x_models import Base
from src.models.platooning_models import PlatoonGroup, PlatoonMember
from src.api.v1.platooning import router, get_db

# Setup in-memory DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

@pytest_asyncio.fixture
async def db_session():
    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[PlatoonGroup.__table__, PlatoonMember.__table__]
        )

    async with TestingSessionLocal() as session:
        yield session

    # テーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.drop_all,
            tables=[PlatoonGroup.__table__, PlatoonMember.__table__]
        )

app = FastAPI()
app.include_router(router)

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_group(client):
    payload = {
        "leader_vehicle_id": "veh-001",
        "max_members": 5,
        "target_speed": 20.0,
        "spacing_distance": 15.0
    }
    response = await client.post("/platooning/groups", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["leader_id"] == "veh-001"
    assert data["status"] == "forming"
    assert data["member_count"] == 1

@pytest.mark.asyncio
async def test_join_and_status(client):
    # 1. Create group
    payload = {
        "leader_vehicle_id": "veh-leader",
        "max_members": 3,
        "target_speed": 25.0
    }
    res = await client.post("/platooning/groups", json=payload)
    assert res.status_code == 201
    group_id = res.json()["id"]

    # 2. Join
    join_payload = {
        "vehicle_id": "veh-follower-1",
        "position": 2
    }
    join_res = await client.post(f"/platooning/groups/{group_id}/join", json=join_payload)
    assert join_res.status_code == 200
    assert join_res.json()["vehicle_id"] == "veh-follower-1"

    # 3. Status
    status_res = await client.get(f"/platooning/groups/{group_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["group"]["member_count"] == 2
    assert len(status_data["members"]) == 2

@pytest.mark.asyncio
async def test_leave_group(client):
    # Create and join
    create_res = await client.post("/platooning/groups", json={
        "leader_vehicle_id": "L1", "max_members": 3, "target_speed": 10
    })
    group_id = create_res.json()["id"]

    await client.post(f"/platooning/groups/{group_id}/join", json={
        "vehicle_id": "F1", "position": 2
    })

    # Leave
    leave_res = await client.delete(f"/platooning/groups/{group_id}/leave?vehicle_id=F1")
    assert leave_res.status_code == 200

    # Verify count
    status_res = await client.get(f"/platooning/groups/{group_id}/status")
    assert status_res.json()["group"]["member_count"] == 1 # Only leader left

@pytest.mark.asyncio
async def test_commands(client):
    create_res = await client.post("/platooning/groups", json={
        "leader_vehicle_id": "L2", "max_members": 3, "target_speed": 10
    })
    group_id = create_res.json()["id"]

    # Brake
    brake_res = await client.put(f"/platooning/groups/{group_id}/command", json={"action": "brake"})
    assert brake_res.status_code == 200

    status_res = await client.get(f"/platooning/groups/{group_id}/status")
    assert status_res.json()["group"]["status"] == "emergency_braking"

    # Dissolve
    dissolve_res = await client.put(f"/platooning/groups/{group_id}/command", json={"action": "dissolve"})
    assert dissolve_res.status_code == 200

    status_res = await client.get(f"/platooning/groups/{group_id}/status")
    assert status_res.json()["group"]["status"] == "dissolved"
    assert status_res.json()["group"]["member_count"] == 0
    assert len(status_res.json()["members"]) == 0
