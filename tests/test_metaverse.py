import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.metaverse_models import VirtualSpace, Avatar, SpaceType, AssetType

@pytest.mark.asyncio
async def test_create_space(client: AsyncClient):
    response = await client.post("/spaces/create", json={
        "name": "Test World",
        "owner_id": 1,
        "max_occupancy": 50,
        "space_type": "world"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test World"
    assert data["status"] == "created"
    assert "id" in data

@pytest.mark.asyncio
async def test_join_space_creates_avatar(client: AsyncClient, db_session: AsyncSession):
    # First create a space
    space = VirtualSpace(name="Lobby", owner_id=1, space_type=SpaceType.room)
    db_session.add(space)
    await db_session.commit()
    await db_session.refresh(space)

    # Join the space
    response = await client.post(f"/spaces/{space.id}/join", json={
        "avatar_id": 100,
        "user_id": 10,
        "initial_x": 10.0,
        "initial_y": 0.0,
        "initial_z": 5.0
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "joined"
    assert data["space_id"] == space.id
    assert data["position"]["x"] == 10.0

    # Check occupants
    resp_occ = await client.get(f"/spaces/{space.id}/occupants")
    assert resp_occ.status_code == 200
    occupants = resp_occ.json()
    assert len(occupants) == 1
    assert occupants[0]["display_name"] == "User_10"

@pytest.mark.asyncio
async def test_place_asset(client: AsyncClient, db_session: AsyncSession):
    space = VirtualSpace(name="Gallery", owner_id=2, space_type=SpaceType.event)
    db_session.add(space)
    await db_session.commit()

    asset_payload = {
        "asset_id": "model_123",
        "position": {"x": 1, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1},
        "rotation": {"x": 0, "y": 90, "z": 0}
    }

    response = await client.post(f"/spaces/{space.id}/place-asset", json=asset_payload)
    assert response.status_code == 200
    assert response.json()["asset_count"] == 1

    # Check manifest
    resp_man = await client.get(f"/spaces/{space.id}/asset-manifest")
    assert resp_man.status_code == 200
    manifest = resp_man.json()
    assert len(manifest["placed_assets"]) == 1
    assert manifest["placed_assets"][0]["asset_id"] == "model_123"

@pytest.mark.asyncio
async def test_broadcast_event(client: AsyncClient):
    # Create space first via API
    resp_create = await client.post("/spaces/create", json={"name": "Event Hall", "owner_id": 1})
    space_id = resp_create.json()["id"]

    response = await client.post(f"/spaces/{space_id}/broadcast-event", json={
        "event_type": "fireworks",
        "payload": {"duration": 10}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "broadcasted"

@pytest.mark.asyncio
async def test_occupancy_limit(client: AsyncClient, db_session: AsyncSession):
    space = VirtualSpace(name="Tiny Room", owner_id=1, max_occupancy=1)
    db_session.add(space)
    await db_session.commit()
    await db_session.refresh(space)

    # User 1 joins
    resp1 = await client.post(f"/spaces/{space.id}/join", json={
        "avatar_id": 1,
        "user_id": 1,
        "initial_x": 0.0, "initial_y": 0.0, "initial_z": 0.0
    })
    assert resp1.status_code == 200

    # User 2 joins (should fail)
    resp2 = await client.post(f"/spaces/{space.id}/join", json={
        "avatar_id": 2,
        "user_id": 2,
        "initial_x": 0.0, "initial_y": 0.0, "initial_z": 0.0
    })
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Space is full"
