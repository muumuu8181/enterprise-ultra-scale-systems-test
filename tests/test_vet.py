from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db
from src.main import app
import os
import pytest

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Drop tables to start fresh
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_workflow():
    # 1. Create Pet
    response = client.post(
        "/api/v1/vet/pets",
        json={
            "name": "Buddy",
            "species": "dog",
            "owner_id": "owner123"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Buddy"
    pet_id = data["id"]

    # 2. List Pets
    response = client.get("/api/v1/vet/pets")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # 3. Book Appointment
    response = client.post(
        "/api/v1/vet/appointments/book",
        json={
            "pet_id": pet_id,
            "vet_id": "vet123",
            "appointment_type": "checkup",
            "scheduled_at": "2023-10-27T10:00:00"
        }
    )
    assert response.status_code == 201
    appt_data = response.json()
    assert appt_data["pet_id"] == pet_id
    appt_id = appt_data["id"]

    # 4. Create Medical Record
    response = client.post(
        "/api/v1/vet/records/create",
        json={
            "pet_id": pet_id,
            "appointment_id": appt_id,
            "diagnosis": "Healthy",
            "treatments": ["checkup"],
            "vitals": {"weight": 20.5}
        }
    )
    assert response.status_code == 201
    record_data = response.json()
    assert record_data["diagnosis"] == "Healthy"

    # 5. Get Medical History
    response = client.get(f"/api/v1/vet/pets/{pet_id}/medical-history")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # 6. Check Inventory (Mocked)
    response = client.get("/api/v1/vet/inventory/medications?low_stock=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["low_stock"] is True

    # 7. Check Revenue (Mocked)
    response = client.get("/api/v1/vet/analytics/revenue")
    assert response.status_code == 200
    assert "revenue" in response.json()
