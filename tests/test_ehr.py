import pytest
from src.models.ehr_models import PatientRecord, LabOrder, ReferralLetter, ReferralUrgency, LabStatus

@pytest.mark.asyncio
async def test_create_and_get_patient_record(client):
    record_data = {
        "patient_id": "P123",
        "allergies": {"penicillin": "rash"},
        "chronic_conditions": {"hypertension": "managed"},
        "medications": {"lisinopril": "10mg"},
        "blood_type": "O+",
        "emergency_contact": "Jane Doe"
    }

    # Create via PUT (upsert)
    response = await client.put("/api/v1/ehr/patients/P123/record", json=record_data)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "P123"
    assert data["blood_type"] == "O+"

    # Get
    response = await client.get("/api/v1/ehr/patients/P123/record")
    assert response.status_code == 200
    assert response.json()["allergies"]["penicillin"] == "rash"

@pytest.mark.asyncio
async def test_create_lab_order(client):
    order_data = {
        "consultation_id": "C456",
        "tests": {"cbc": "routine"},
        "lab_id": "LAB01"
    }
    response = await client.post("/api/v1/ehr/lab-orders", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ordered"
    assert data["id"] is not None

    order_id = data["id"]
    # Get results
    response = await client.get(f"/api/v1/ehr/lab-orders/{order_id}/results")
    assert response.status_code == 200
    assert response.json()["status"] == "ordered"

@pytest.mark.asyncio
async def test_referral_acceptance(client, db_session):
    # Setup: Create a referral manually
    referral = ReferralLetter(
        patient_id="P999", # Added
        consultation_id="C789",
        referred_to_specialty="Cardiology",
        urgency=ReferralUrgency.routine,
        clinical_summary="Check heart",
        accepted=False
    )
    db_session.add(referral)
    await db_session.commit()
    await db_session.refresh(referral)

    ref_id = referral.id

    # Accept
    payload = {"referral_id": ref_id, "accepted": True}
    response = await client.post("/api/v1/ehr/referrals/accept", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is True

    # Verify in DB
    await db_session.refresh(referral)
    assert referral.accepted is True

@pytest.mark.asyncio
async def test_get_patient_referrals(client, db_session):
    # Create two referrals for different patients
    ref1 = ReferralLetter(
        patient_id="P1",
        consultation_id="C1",
        referred_to_specialty="Derma",
        urgency=ReferralUrgency.routine,
        clinical_summary="Rash",
        accepted=False
    )
    ref2 = ReferralLetter(
        patient_id="P2",
        consultation_id="C2",
        referred_to_specialty="Ortho",
        urgency=ReferralUrgency.routine,
        clinical_summary="Bone",
        accepted=False
    )
    db_session.add_all([ref1, ref2])
    await db_session.commit()

    # Fetch P1 referrals
    response = await client.get("/api/v1/ehr/patients/P1/referrals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == "P1"
    assert data[0]["referred_to_specialty"] == "Derma"

    # Fetch P2 referrals
    response = await client.get("/api/v1/ehr/patients/P2/referrals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == "P2"
