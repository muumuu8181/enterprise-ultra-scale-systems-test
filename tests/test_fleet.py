import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.fleet import router
from src.core.database import get_db
from src.models.fleet_models import FleetTask
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Setup generic FastAPI app for testing
app = FastAPI()
app.include_router(router)

client = TestClient(app)

# Helper to mock db refresh
async def mock_refresh(instance):
    instance.id = 1
    if isinstance(instance, FleetTask):
        instance.assigned_at = datetime.now()

@pytest.mark.asyncio
async def test_create_vehicle():
    # Mock DB session
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)

    # Override dependency
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post("/fleet/vehicles", json={
        "fleet_id": 1,
        "vehicle_id": "v123",
        "model": "Toyota Prius",
        "purpose": "taxi"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == "v123"
    assert data["fleet_id"] == 1
    assert data["status"] == "active"
    assert data["id"] == 1

@pytest.mark.asyncio
async def test_get_analytics():
    mock_db = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock FleetOptimizer.generate_fleet_report
    with patch("src.api.v1.fleet.optimizer.generate_fleet_report", new_callable=AsyncMock) as mock_report:
        mock_report.return_value = {
            "fleet_id": 1,
            "generated_at": "2023-01-01T00:00:00",
            "total_vehicles": 10,
            "total_distance_km": 1000.0,
            "estimated_fuel_consumption_liters": 100.0,
            "total_idling_hours": 5.0,
            "status": "generated"
        }

        response = client.get("/fleet/1/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_vehicles"] == 10
        assert data["total_distance_km"] == 1000.0

@pytest.mark.asyncio
async def test_create_task():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock the execute result for finding vehicle
    mock_result = MagicMock()
    mock_vehicle = MagicMock()
    mock_vehicle.fleet_id = 1
    mock_vehicle.id = 100
    mock_result.scalar_one_or_none.return_value = mock_vehicle
    mock_db.execute.return_value = mock_result

    response = client.post("/fleet/tasks", json={
        "vehicle_id": "v123",
        "task_type": "delivery",
        "destination": {"lat": 35.6895, "lon": 139.6917},
        "priority": 1
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["vehicle_id"] == 100 # from mocked vehicle
