from fastapi.testclient import TestClient
from src.api.v1.charging import router
from fastapi import FastAPI
import pytest

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_get_nearby_stations():
    response = client.get("/stations/nearby?lat=35.6895&lon=139.6917")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "Station A"

def test_get_station_availability():
    response = client.get("/stations/1/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 1
    assert "available_chargers" in data

def test_start_session():
    payload = {
        "charger_id": 1,
        "user_id": "user123",
        "vehicle_id": "veh123",
        "payment_method": "credit_card"
    }
    response = client.post("/sessions/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["charger_id"] == 1

def test_stop_session():
    response = client.post("/sessions/123/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"

def test_report_fault():
    payload = {
        "reason": "broken_screen",
        "description": "The screen is cracked"
    }
    response = client.post("/chargers/1/report-fault", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fault_reported"
