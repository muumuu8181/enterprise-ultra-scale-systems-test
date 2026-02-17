import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.building_twin import Base, BuildingTwin, FloorPlan, EnergyReading
from src.services.building_service import optimize_hvac, predict_energy_consumption, simulate_evacuation
from src.api.v1.buildings import router

# Setup App
app = FastAPI()
app.include_router(router)

client = TestClient(app)

# Test Models
def test_models():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    twin = BuildingTwin(
        twin_id="TWIN-001",
        floors=5,
        total_area_sqm=1000.0,
        occupancy_current=50,
        hvac_zones={"zone1": "cool", "zone2": "heat"},
        energy_kwh_today=120.5
    )
    session.add(twin)
    session.commit()

    retrieved = session.query(BuildingTwin).filter_by(twin_id="TWIN-001").first()
    assert retrieved is not None
    assert retrieved.floors == 5
    assert retrieved.hvac_zones["zone1"] == "cool"

# Test Services
@pytest.mark.asyncio
async def test_services():
    hvac = await optimize_hvac(1, 0.8)
    assert hvac.building_id == 1
    assert hvac.optimized_savings > 0

    consumption = await predict_energy_consumption(1, 24)
    assert len(consumption) == 24

    plan = await simulate_evacuation(1, "fire")
    assert plan.building_id == 1
    assert plan.emergency_type == "fire"

# Test API
def test_api_energy_dashboard():
    response = client.get("/buildings/1/energy-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["building_id"] == 1
    assert "predicted_24h" in data

def test_api_hvac_optimize():
    response = client.post("/buildings/1/hvac-optimize", json={"comfort_weight": 0.5})
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data

def test_api_occupancy_heatmap():
    response = client.get("/buildings/1/occupancy-heatmap")
    assert response.status_code == 200
    data = response.json()
    assert "heatmap" in data

def test_api_emergency_mode():
    response = client.post("/buildings/1/emergency-mode", json={"emergency_type": "earthquake"})
    assert response.status_code == 200
    data = response.json()
    assert data["emergency_type"] == "earthquake"

def test_api_carbon_footprint():
    response = client.get("/buildings/1/carbon-footprint")
    assert response.status_code == 200

def test_api_schedule_maintenance():
    response = client.post("/buildings/1/schedule-maintenance", json={"date": "2023-10-27", "description": "fix ac"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scheduled"
