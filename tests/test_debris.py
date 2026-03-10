import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.api.v1.debris import router, get_db
from src.models.debris_models import DebrisObjectType, ConjunctionStatus, ManeuverStatus
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

class MockObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.mark.asyncio
async def test_get_objects():
    mock_db = AsyncMock()
    mock_result = MagicMock()

    obj = MockObj(
        id=1,
        norad_id=123,
        object_type=DebrisObjectType.payload,
        size_cm=10.0,
        mass_kg=100.0,
        orbit_altitude_km=500.0,
        inclination_deg=45.0,
        tle_line1="line1",
        tle_line2="line2",
        last_observed=datetime.utcnow()
    )

    mock_result.scalars.return_value.all.return_value = [obj]
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.get("/objects")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["norad_id"] == 123

@pytest.mark.asyncio
async def test_assess_conjunction_alert():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    async def side_effect_refresh(obj):
        obj.id = 1
    mock_db.refresh.side_effect = side_effect_refresh

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "primary_object_id": 1,
        "secondary_object_id": 2,
        "tca": datetime.utcnow().isoformat(),
        "miss_distance_m": 100.0,
        "collision_probability": 0.05
    }
    response = client.post("/conjunctions/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alert"
    assert data["id"] == 1

@pytest.mark.asyncio
async def test_assess_conjunction_warning():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    async def side_effect_refresh(obj):
        obj.id = 2
    mock_db.refresh.side_effect = side_effect_refresh

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "primary_object_id": 1,
        "secondary_object_id": 2,
        "tca": datetime.utcnow().isoformat(),
        "miss_distance_m": 500.0,
        "collision_probability": 0.005
    }
    response = client.post("/conjunctions/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "warning"
    assert data["id"] == 2

@pytest.mark.asyncio
async def test_plan_maneuver():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    async def side_effect_refresh(obj):
        obj.id = 3
    mock_db.refresh.side_effect = side_effect_refresh

    mock_conjunction = AsyncMock()
    mock_db.get.return_value = mock_conjunction

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "conjunction_id": 1,
        "satellite_id": 1,
        "delta_v": 1.5,
        "burn_duration_sec": 30.0,
        "execution_time": datetime.utcnow().isoformat(),
        "fuel_cost_kg": 5.0
    }
    response = client.post("/maneuvers/plan", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "planned"
    assert response.json()["id"] == 3
