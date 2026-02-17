import pytest
from datetime import date, timedelta
from src.models.pet_models import Species, Vaccination

@pytest.mark.asyncio
async def test_register_pet(client):
    payload = {
        "owner_id": 1,
        "name": "Buddy",
        "species": "dog",
        "breed": "Golden Retriever",
        "birthdate": "2020-01-01",
        "weight_kg": 30.0,
        "microchip_id": "123456789"
    }
    response = await client.post("/pets/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Buddy"
    assert data["species"] == "dog"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_weight_log_anomaly(client):
    # Register pet
    payload = {
        "owner_id": 1,
        "name": "Tiny",
        "species": "cat",
        "birthdate": "2020-01-01",
        "weight_kg": 4.0
    }
    create_res = await client.post("/pets/register", json=payload)
    pet_id = create_res.json()["id"]

    # Log normal weight
    log_payload = {"weight_kg": 4.5}
    res = await client.post(f"/pets/{pet_id}/weight-log", json=log_payload)
    assert res.status_code == 200
    assert res.json() is None  # No anomaly

    # Log abnormal weight (e.g. 25kg for a cat)
    log_payload = {"weight_kg": 25.0}
    res = await client.post(f"/pets/{pet_id}/weight-log", json=log_payload)
    assert res.status_code == 200
    anomaly = res.json()
    assert anomaly is not None
    assert anomaly["severity"] == "High"
    assert "Abnormal weight" in anomaly["message"]

@pytest.mark.asyncio
async def test_health_summary_and_vaccines(client, db_session):
    # Register pet
    payload = {
        "owner_id": 1,
        "name": "Rex",
        "species": "dog",
        "birthdate": "2019-01-01",
        "weight_kg": 25.0
    }
    create_res = await client.post("/pets/register", json=payload)
    pet_id = create_res.json()["id"]

    # Seed vaccinations directly
    v1 = Vaccination(
        pet_id=pet_id,
        vaccine_name="Rabies",
        administered_date=date.today() - timedelta(days=365),
        next_due=date.today() + timedelta(days=1), # Upcoming
        batch_number="B123"
    )
    v2 = Vaccination(
        pet_id=pet_id,
        vaccine_name="Distemper",
        administered_date=date.today() - timedelta(days=400),
        next_due=date.today() - timedelta(days=1), # Overdue
        batch_number="B124"
    )
    db_session.add_all([v1, v2])
    await db_session.commit()

    # Test /vaccination-passport
    res = await client.get(f"/pets/{pet_id}/vaccination-passport")
    assert res.status_code == 200
    vaccines = res.json()
    assert len(vaccines) == 2
    names = {v["vaccine_name"] for v in vaccines}
    assert "Rabies" in names
    assert "Distemper" in names

    # Test /reminders
    res = await client.get(f"/pets/{pet_id}/reminders")
    assert res.status_code == 200
    reminders = res.json()
    assert len(reminders) == 2

    rabies_rem = next(r for r in reminders if r["vaccine_name"] == "Rabies")
    assert rabies_rem["overdue"] is False

    distemper_rem = next(r for r in reminders if r["vaccine_name"] == "Distemper")
    assert distemper_rem["overdue"] is True

    # Test /health-summary
    res = await client.get(f"/pets/{pet_id}/health-summary")
    assert res.status_code == 200
    report = res.json()
    assert report["pet_info"]["name"] == "Rex"
    assert len(report["vaccination_status"]) == 2
    assert len(report["upcoming_vaccines"]) == 2
