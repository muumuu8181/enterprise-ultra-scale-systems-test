import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.services.distribution_service import optimize_distribution, track_cold_chain, flag_compromised_batch
from src.core.database import engine, Base, AsyncSessionLocal
from src.models.vaccine_models import DistributionCenter

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_receive_batch():
    # Create a DistributionCenter first to satisfy FK constraints
    async with AsyncSessionLocal() as session:
        dc = DistributionCenter(
            id=1,
            name="Central Hub",
            location={"type": "Point", "coordinates": [0, 0]},
            storage_capacity=10000,
            cold_chain_certified=True,
            current_inventory={}
        )
        session.add(dc)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/batches/receive", json={
            "vaccine_type": "Pfizer",
            "manufacturer": "Pfizer Inc.",
            "lot_number": "LOT12345",
            "quantity": 1000,
            "expiry_date": "2025-12-31T00:00:00Z",
            "cold_chain_required": True,
            "current_location_id": 1
        })
    assert response.status_code == 200
    data = response.json()
    assert data["lot_number"] == "LOT12345"
    assert data["quantity"] == 1000

@pytest.mark.asyncio
async def test_chain_of_custody():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/batches/123/chain-of-custody")
    assert response.status_code == 200
    assert response.json()["batch_id"] == 123

@pytest.mark.asyncio
async def test_expiring_soon():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/batches/expiring-soon")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_transfer_batch():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/batches/1/transfer", json={
            "destination_location_id": 2,
            "quantity": 500
        })
    assert response.status_code == 200
    assert response.json()["status"] == "transfer_initiated"

@pytest.mark.asyncio
async def test_service_logic():
    log = await track_cold_chain(123)
    assert log.batch_id == 123
    assert not log.is_compromised

    plan = await optimize_distribution({"demand": 1000})
    assert plan.plan_id == "plan-123"

    flag = await flag_compromised_batch(123, "Too hot")
    assert flag["status"] == "compromised"
