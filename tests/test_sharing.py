from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.sharing import router
from src.models.sharing_models import Vehicle, VehicleType, VehicleStatus

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_read_vehicles_nearby():
    response = client.get("/vehicles/nearby?lat=35.0&lon=139.0")
    # Note: Router has no prefix in the file I wrote, but usually it's mounted under /api/v1/sharing or similar.
    # But in the test I'm mounting router directly to app, so path matches router definitions.
    # Wait, in src/api/v1/sharing.py I defined router = APIRouter(tags=["sharing"]).
    # I did NOT set a prefix in the APIRouter constructor.
    # So paths are /vehicles/nearby etc.
    assert response.status_code == 200
    assert response.json() == []

def test_unlock_vehicle():
    response = client.post("/vehicles/1/unlock")
    assert response.status_code == 200
    assert response.json()["status"] == "rented"

def test_start_ride():
    payload = {
        "vehicle_id": 1,
        "user_id": 123,
        "start_location": {
            "type": "Point",
            "coordinates": [139.0, 35.0]
        }
    }
    response = client.post("/rides/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 123
    assert data["status"] == "active"

def test_model_instantiation():
    v = Vehicle(
        vehicle_type=VehicleType.BIKE,
        serial_number="123",
        status=VehicleStatus.AVAILABLE
    )
    assert v.vehicle_type == VehicleType.BIKE
