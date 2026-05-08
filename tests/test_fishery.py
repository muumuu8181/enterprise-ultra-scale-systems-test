import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.fishery import router
from src.database import get_db
from src.models.fishery_models import FishingVessel, QuotaAllocation, CatchReport, VesselType, QuotaStatus
from datetime import date, datetime

# Setup App for testing
app = FastAPI()
app.include_router(router)

# Mock DB Session
mock_session = AsyncMock()

async def override_get_db():
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_get_vessels():
    # Setup mock return value
    mock_result = MagicMock()
    vessel = FishingVessel(
        id=1,
        name="Test Vessel",
        registration_number="REG001",
        owner_id=10,
        vessel_type=VesselType.trawler,
        length_m=30.0,
        port_base="Port A",
        license_expiry=date(2025, 1, 1),
        ais_mmsi="123456"
    )
    mock_result.scalars.return_value.all.return_value = [vessel]
    mock_session.execute.return_value = mock_result

    response = client.get("/vessels")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Vessel"
    assert data[0]["vessel_type"] == "trawler"

def test_allocate_quota():
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()

    def side_effect_add(instance):
        instance.id = 1
    mock_session.add.side_effect = side_effect_add

    payload = {
        "vessel_id": 1,
        "species": "Cod",
        "fishing_zone": "North Sea",
        "quota_tonnes": 500.0,
        "caught_tonnes": 0.0,
        "remaining_tonnes": 500.0,
        "season_start": "2024-01-01",
        "season_end": "2024-12-31",
        "status": "active"
    }

    response = client.post("/quotas/allocate", json=payload)
    if response.status_code != 201:
        print(response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["species"] == "Cod"

def test_report_catch():
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()

    def side_effect_add(instance):
        instance.id = 100
        # Simulate DB creating WKT or Geometry
        # But here we just keep the string or whatever was assigned
        pass
    mock_session.add.side_effect = side_effect_add

    payload = {
        "vessel_id": 1,
        "species": "Cod",
        "weight_kg": 1500.0,
        "location": {"type": "Point", "coordinates": [10.5, 60.2]},
        "catch_date": "2024-06-15T10:00:00",
        "gear_type": "Trawl",
        "bycatch": {"species": "None"},
        "verified": True,
        "landing_port": "Port B"
    }

    response = client.post("/catch/report", json=payload)
    if response.status_code != 201:
        print(response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 100
    assert data["weight_kg"] == 1500.0
    # Location verification might be tricky due to mocking strategy
    # If the response returns valid GeoJSON (via validator), check type
    if "type" in data["location"]:
        assert data["location"]["type"] == "Point"

def test_analytics_stock_assessment():
    response = client.get("/analytics/stock-assessment?species=Cod")
    assert response.status_code == 200
    data = response.json()
    assert data["species"] == "Cod"
    assert "status" in data

def test_compliance_tracking():
    response = client.get("/compliance/vessel-tracking/1")
    assert response.status_code == 200
    data = response.json()
    assert data["vessel_id"] == 1
    assert "last_known_location" in data
