import pytest
from datetime import date

@pytest.mark.asyncio
async def test_create_artifact(client):
    response = await client.post("/api/v1/artifacts", json={
        "accession_number": "A123",
        "title": "Ancient Vase",
        "artist_creator": "Unknown",
        "period": "Roman",
        "medium": "Ceramic",
        "dimensions": "10x10x20cm",
        "provenance": [{"year": 2020, "owner": "Museum"}],
        "location_gallery": "Gallery A",
        "condition": "good",
        "insurance_value": 1000.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Ancient Vase"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_get_artifacts(client):
    # Depending on test order, artifact might already exist or not.
    # But since session is per function in some setups or per session, let's create one first just in case
    await client.post("/api/v1/artifacts", json={
        "accession_number": "B456",
        "title": "Painting",
        "artist_creator": "Da Vinci",
        "period": "Renaissance",
        "medium": "Oil",
        "dimensions": "50x50cm",
        "provenance": [],
        "location_gallery": "Gallery B",
        "condition": "excellent",
        "insurance_value": 5000000.0
    })

    response = await client.get("/api/v1/artifacts?period=Renaissance")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    found = False
    for item in data:
        if item["period"] == "Renaissance":
            found = True
            break
    assert found

@pytest.mark.asyncio
async def test_create_exhibition(client):
    response = await client.post("/api/v1/exhibitions/create", json={
        "title": "Renaissance Art",
        "curator_id": 1,
        "theme": "Art",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "galleries": ["Gallery B"],
        "artifact_ids": [1],
        "status": "planning"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Renaissance Art"

@pytest.mark.asyncio
async def test_loan_request(client):
    # First create artifact
    art_resp = await client.post("/api/v1/artifacts", json={
        "accession_number": "L001",
        "title": "Loan Item",
        "artist_creator": "Me",
        "period": "Modern",
        "medium": "Plastic",
        "dimensions": "1x1cm",
        "location_gallery": "Storage",
        "condition": "fair",
        "insurance_value": 10.0
    })
    assert art_resp.status_code == 200
    artifact_id = art_resp.json()["id"]

    response = await client.post("/api/v1/loans/request", json={
        "artifact_id": artifact_id,
        "borrower_institution": "Other Museum",
        "purpose": "Exhibition",
        "loan_start": "2024-01-01",
        "loan_end": "2024-02-01",
        "insurance_amount": 100.0
    })
    assert response.status_code == 200
    assert response.json()["status"] == "requested"

@pytest.mark.asyncio
async def test_conservation_log(client):
    art_resp = await client.post("/api/v1/artifacts", json={
        "accession_number": "C001",
        "title": "Broken Item",
        "artist_creator": "Me",
        "period": "Modern",
        "medium": "Glass",
        "dimensions": "10x10cm",
        "location_gallery": "Lab",
        "condition": "poor",
        "insurance_value": 50.0
    })
    assert art_resp.status_code == 200
    artifact_id = art_resp.json()["id"]

    # Report
    report_resp = await client.post("/api/v1/conservation/report", json={
        "artifact_id": artifact_id,
        "log_date": "2023-10-27",
        "description": "Repaired crack",
        "reporter": "Restorer X",
        "new_condition": "fair"
    })
    assert report_resp.status_code == 200

    # Check log
    log_resp = await client.get(f"/api/v1/conservation/{artifact_id}/condition-log")
    assert log_resp.status_code == 200
    assert len(log_resp.json()) >= 1
    assert log_resp.json()[0]["description"] == "Repaired crack"
