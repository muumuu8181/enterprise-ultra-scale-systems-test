import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from src.services.preservation_service import PreservationService

@pytest.mark.asyncio
async def test_register_item(client: AsyncClient):
    payload = {
        "title": "Ancient Scroll",
        "item_type": "document",
        "origin": "Egypt",
        "condition": "fair",
        "date_created": datetime.now(timezone.utc).isoformat()
    }
    response = await client.post("/api/v1/items/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Ancient Scroll"
    assert data["item_type"] == "document"
    assert data["condition"] == "fair"
    assert data["digitized"] is False

@pytest.mark.asyncio
async def test_create_collection(client: AsyncClient):
    payload = {
        "name": "Treasures of the Nile",
        "owner_institution": "National Museum",
        "public_access": True
    }
    response = await client.post("/api/v1/collections", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Treasures of the Nile"
    assert data["item_count"] == 0

@pytest.mark.asyncio
async def test_search_items(client: AsyncClient):
    # Register items
    item1 = {
        "title": "Scroll 1",
        "item_type": "document",
        "origin": "Egypt",
        "condition": "good",
        "date_created": datetime.now(timezone.utc).isoformat()
    }
    await client.post("/api/v1/items/register", json=item1)

    response = await client.get("/api/v1/items/search?query=Scroll")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Scroll 1"

@pytest.mark.asyncio
async def test_service_methods():
    service = PreservationService()
    report = await service.assess_condition(1)
    assert report.item_id == 1
    assert report.condition == "good"
