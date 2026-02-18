from fastapi.testclient import TestClient
from src.main import app
from src.core.database import SessionLocal, Base, engine
from src.models.rental_models import Vehicle, Booking
import pytest
from datetime import datetime, timedelta
import os

# Use a clean DB for this test module
TEST_DB = "./test_telematics.db"
# Override the engine in main app? No, simpler to just use the one configured but maybe reset it.
# Actually, since we can't easily override the global engine without dependency injection override or patching,
# we'll just rely on the fact that we can drop_all/create_all.

@pytest.fixture(scope="module")
def client():
    # Setup
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create test data
    # We need to make sure we don't duplicate IDs if other tests ran
    # But since we drop_all, it's clean.

    vehicle = Vehicle(id=1, status="rented", fuel_level=100.0)
    db.add(vehicle)

    booking = Booking(id=1, vehicle_id=1, start_time=datetime.utcnow() - timedelta(hours=1), status="active")
    db.add(booking)

    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c

    # Teardown
    Base.metadata.drop_all(bind=engine)

def test_telematics_flow(client):
    # Update location
    response = client.post("/telematics/1/location", json={
        "latitude": 35.6895,
        "longitude": 139.6917,
        "speed": 60.0,
        "fuel_level": 95.0
    })
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "updated"}

    # Get trip summary
    response = client.get("/telematics/1/trip-summary")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["booking_id"] == 1
    assert data["total_distance"] >= 1.0 # At least 1 log
    assert data["average_speed"] == 60.0

    # Create alert
    response = client.post("/telematics/1/alert", json={
        "type": "breakdown",
        "details": "Engine smoke"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "alert_received"
