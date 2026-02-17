from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.transplant import router
from src.models.transplant_models import WaitlistEntry, OrganType, WaitlistStatus
import pytest

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_get_waitlist():
    response = client.get("/waitlist")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "patient_id" in data[0]
        assert "organ_needed" in data[0]

def test_get_waitlist_position():
    response = client.get("/waitlist/123/position")
    assert response.status_code == 200
    assert "position" in response.json()

def test_register_organ():
    organ_data = {
        "donor_id": "D123",
        "donor_type": "living",
        "organ_type": "kidney",
        "blood_type": "O+",
        "hla_typing": {"locus_a": "02:01"},
        "condition_score": 90
    }
    response = client.post("/donors/register-organ", json=organ_data)
    assert response.status_code == 200
    assert response.json()["donor_id"] == "D123"
    assert response.json()["organ_type"] == "kidney"

def test_run_matching():
    matching_data = {
        "organ_id": 101,
        "algorithm_version": "v2.0"
    }
    response = client.post("/matching/run", json=matching_data)
    assert response.status_code == 200
    assert response.json()["status"] == "Match Found"

def test_model_instantiation():
    entry = WaitlistEntry(
        patient_id="P123",
        organ_needed=OrganType.heart,
        blood_type="AB+",
        urgency_score=10,
        transplant_center_id="TC1",
        status=WaitlistStatus.active
    )
    assert entry.patient_id == "P123"
    assert entry.organ_needed == OrganType.heart
    assert entry.status == WaitlistStatus.active
