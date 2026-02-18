import pytest
from httpx import AsyncClient
from sqlalchemy import select
from src.models.parcel_models import Parcel

@pytest.mark.asyncio
async def test_create_shipment(client: AsyncClient):
    payload = {
        "sender_id": 1,
        "recipient_address": {"street": "123 Main St", "city": "Test City", "zip": "12345"},
        "weight_kg": 2.5,
        "dimensions": {"l": 10, "w": 10, "h": 10},
        "service_type": "standard",
        "carrier": "fedex"
    }
    response = await client.post("/api/v1/parcels/create-shipment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "tracking_number" in data
    assert data["carrier"] == "fedex"
    assert "label_url" in data
    assert "estimated_delivery" in data

@pytest.mark.asyncio
async def test_track_parcel(client: AsyncClient):
    response = await client.get("/api/v1/parcels/TRACK123/track?carrier=fedex")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["event_type"] == "picked_up"

@pytest.mark.asyncio
async def test_batch_track(client: AsyncClient):
    payload = {"tracking_numbers": ["T1", "T2"]}
    response = await client.post("/api/v1/parcels/batch-track", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "T1" in data
    assert "T2" in data
    assert len(data["T1"]) > 0

@pytest.mark.asyncio
async def test_redirect_parcel(client: AsyncClient):
    payload = {
        "sender_id": 1,
        "recipient_address": {"street": "123 Main St", "city": "Test City", "zip": "12345"},
        "weight_kg": 2.5,
        "dimensions": {"l": 10, "w": 10, "h": 10},
        "service_type": "standard",
        "carrier": "fedex"
    }
    create_response = await client.post("/api/v1/parcels/create-shipment", json=payload)
    assert create_response.status_code == 200
    tracking_number = create_response.json()["tracking_number"]

    redirect_payload = {
        "new_address": {"street": "456 Other St", "city": "New City", "zip": "67890"}
    }
    response = await client.post(f"/api/v1/parcels/{tracking_number}/redirect", json=redirect_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_get_label(client: AsyncClient, db_session):
    payload = {
        "sender_id": 1,
        "recipient_address": {"street": "123 Main St", "city": "Test City", "zip": "12345"},
        "weight_kg": 2.5,
        "dimensions": {"l": 10, "w": 10, "h": 10},
        "service_type": "standard",
        "carrier": "fedex"
    }
    await client.post("/api/v1/parcels/create-shipment", json=payload)

    result = await db_session.execute(select(Parcel))
    parcel = result.scalars().first()
    assert parcel is not None

    response = await client.get(f"/api/v1/parcels/{parcel.id}/label")
    assert response.status_code == 200
    assert "label_url" in response.json()
