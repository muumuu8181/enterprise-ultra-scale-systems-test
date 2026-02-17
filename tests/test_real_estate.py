import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.services.valuation_service import estimate_value, calculate_mortgage_options

@pytest.mark.asyncio
async def test_create_property():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/properties/list", json={
            "address": "456 Oak St",
            "property_type": "residential",
            "bedrooms": 4,
            "area_sqm": 200.0,
            "year_built": 2015,
            "list_price": 600000.0
        })
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "456 Oak St"
    assert data["id"] == 1
    assert data["status"] == "listed"

@pytest.mark.asyncio
async def test_search_properties():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/properties/search?city=NewYork")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["address"] == "123 Main St"

@pytest.mark.asyncio
async def test_valuation_service():
    val = await estimate_value(1)
    assert val.property_id == 1
    assert val.estimated_value > 0

@pytest.mark.asyncio
async def test_mortgage_calculation():
    scenarios = await calculate_mortgage_options(1, 20.0)
    assert len(scenarios) == 2
    assert scenarios[0].term_years == 30
    assert scenarios[1].term_years == 15

@pytest.mark.asyncio
async def test_submit_offer():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/offers/submit", json={
            "property_id": 1,
            "buyer_id": "user123",
            "offer_price": 550000.0,
            "contingencies": {},
            "expiry_date": "2023-12-31T23:59:59"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["offer_price"] == 550000.0

from src.models.transaction_models import Property, Offer, Escrow

def test_models_import():
    assert Property.__tablename__ == "properties"
    assert Offer.__tablename__ == "offers"
    assert Escrow.__tablename__ == "escrows"

@pytest.mark.asyncio
async def test_search_properties_with_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/properties/search?type=residential")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
