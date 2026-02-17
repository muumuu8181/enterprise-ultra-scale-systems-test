from fastapi.testclient import TestClient
from src.main import app
from src.core.database import SessionLocal, Base, engine
from src.models.rental_models import Booking, DamageClaim, Vehicle
import pytest
from datetime import datetime, timedelta

@pytest.fixture(scope="module")
def client():
    # Setup
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create test data
    # We need a vehicle for the booking constraint? Booking has vehicle_id ForeignKey.
    # So we must create a vehicle first.
    vehicle = Vehicle(id=2, status="rented", fuel_level=100.0)
    db.add(vehicle)

    booking = Booking(id=2, vehicle_id=2, start_time=datetime.utcnow() - timedelta(hours=1), status="active")
    db.add(booking)

    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c

    # Teardown
    Base.metadata.drop_all(bind=engine)

def test_claims_flow(client):
    # Submit claim
    response = client.post("/damage-claims/2", json={
        "description": "Scratched bumper",
        "photos": ["https://example.com/photo1.jpg"]
    })
    assert response.status_code == 200, response.text
    claim_id = response.json()["claim_id"]

    # Get assessment
    response = client.get(f"/damage-claims/{claim_id}/assessment")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "pending"

    # Resolve claim
    response = client.put(f"/damage-claims/{claim_id}/resolve", json={
        "amount": 500.0,
        "assessment_notes": "Minor scratch"
    })
    assert response.status_code == 200, response.text

    # Check resolution
    response = client.get(f"/damage-claims/{claim_id}/assessment")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_amount"] == 500.0
