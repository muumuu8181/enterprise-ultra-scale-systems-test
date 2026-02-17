from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.immigration import router
from src.models.immigration_models import VisaType, ApplicationStatus

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_submit_application():
    response = client.post(
        "/applications/submit",
        json={
            "applicant_id": 1,
            "visa_type": "tourist",
            "destination_country": "Japan",
            "embassy_id": "JP-TOKYO"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["visa_type"] == "tourist"
    assert data["status"] == "submitted"
    assert "id" in data

def test_list_applications():
    response = client.get("/applications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_application_status():
    response = client.get("/applications/1/status")
    assert response.status_code == 200
    assert response.json()["status"] == "submitted"

def test_border_entry_check():
    response = client.post(
        "/border/entry-check",
        json={
            "passport_number": "AB123456",
            "port_of_entry": "NRT",
            "visa_id": 1,
            "customs_declaration": {"item": "none"}
        }
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True

def test_analytics_approval_rates():
    response = client.get("/analytics/approval-rates?period=month")
    assert response.status_code == 200
    assert "approval_rate" in response.json()
