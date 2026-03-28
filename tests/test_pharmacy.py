import pytest
from httpx import AsyncClient
from src.models.pharmacy_models import Medication, Prescription, PrescriptionStatus, MedicationForm
from src.database import get_db

@pytest.mark.asyncio
async def test_create_medication_and_search(client: AsyncClient, db_session):
    # Manually create medication since there is no POST /medications endpoint in requirements
    med = Medication(
        id="med1",
        name="Amoxicillin",
        generic_name="Amoxicillin",
        ndc_code="12345-678-90",
        drug_class="Antibiotic",
        form=MedicationForm.capsule,
        strength="500mg",
        manufacturer="PharmaCorp",
        stock_quantity=100
    )
    db_session.add(med)
    await db_session.commit()

    response = await client.get("/api/v1/pharmacy/medications/search?name=Amoxicillin")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Amoxicillin"
    assert data[0]["form"] == "capsule"

@pytest.mark.asyncio
async def test_receive_prescription(client: AsyncClient, db_session):
    # Need a medication first
    med = Medication(
        id="med2",
        name="Lisinopril",
        generic_name="Lisinopril",
        ndc_code="09876-543-21",
        drug_class="ACE Inhibitor",
        form=MedicationForm.tablet,
        strength="10mg",
        manufacturer="GenericsInc",
        stock_quantity=50
    )
    db_session.add(med)
    await db_session.commit()

    payload = {
        "id": "rx1",
        "patient_id": "pat1",
        "prescriber_id": "doc1",
        "medication_id": "med2",
        "dosage": "10mg",
        "frequency": "Daily",
        "quantity": 30,
        "refills_allowed": 2
    }
    response = await client.post("/api/v1/pharmacy/prescriptions/receive", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["medication_id"] == "med2"

@pytest.mark.asyncio
async def test_check_low_stock(client: AsyncClient, db_session):
    med = Medication(
        id="med3",
        name="LowStockMed",
        generic_name="LowStockGeneric",
        ndc_code="11111-222-33",
        drug_class="Test",
        form=MedicationForm.tablet,
        strength="5mg",
        manufacturer="TestInc",
        stock_quantity=5,
        reorder_level=10
    )
    db_session.add(med)
    await db_session.commit()

    response = await client.get("/api/v1/pharmacy/inventory/low-stock")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "LowStockMed"
