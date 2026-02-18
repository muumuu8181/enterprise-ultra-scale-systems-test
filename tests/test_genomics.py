from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.samples import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_register_sample():
    response = client.post("/samples/register", json={
        "patient_id": "patient_123",
        "sample_type": "blood",
        "sequencing_type": "WGS"
    })
    assert response.status_code == 200
    data = response.json()
    # ID might be greater than 1 if tests run in random order and reuse mock DB
    assert "id" in data
    assert data["patient_id"] == "patient_123"
    assert data["status"] == "received"

def test_get_sample_status():
    # Register a sample first to ensure ID exists
    reg = client.post("/samples/register", json={
        "patient_id": "patient_status_test",
        "sample_type": "blood",
        "sequencing_type": "WGS"
    })
    sample_id = reg.json()["id"]

    response = client.get(f"/samples/{sample_id}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "received"

def test_get_sample_variants():
    # Register a sample first. Mock service returns variants for sample_id=1.
    from src.api.v1.samples import SAMPLES_DB
    SAMPLES_DB.clear() # Reset DB for predictable IDs

    reg = client.post("/samples/register", json={
        "patient_id": "patient_123",
        "sample_type": "blood",
        "sequencing_type": "WGS"
    })
    sample_id = reg.json()["id"]
    assert sample_id == 1

    response = client.get(f"/samples/{sample_id}/variants")
    assert response.status_code == 200
    variants = response.json()
    assert isinstance(variants, list)
    assert len(variants) > 0

def test_get_sample_variants_filtered():
    # Assuming ID 1 exists from previous test or we recreate.
    # Let's reset again to be safe.
    from src.api.v1.samples import SAMPLES_DB
    SAMPLES_DB.clear()

    reg = client.post("/samples/register", json={
        "patient_id": "patient_123",
        "sample_type": "blood",
        "sequencing_type": "WGS"
    })
    sample_id = reg.json()["id"]

    response = client.get(f"/samples/{sample_id}/variants?significance=pathogenic")
    assert response.status_code == 200
    variants = response.json()
    for v in variants:
        assert v["clinvar_significance"] == "pathogenic"

def test_run_pipeline():
    from src.api.v1.samples import SAMPLES_DB
    SAMPLES_DB.clear()

    reg = client.post("/samples/register", json={
        "patient_id": "patient_123",
        "sample_type": "blood",
        "sequencing_type": "WGS"
    })
    sample_id = reg.json()["id"]

    # Updated to send JSON body
    response = client.post("/pipelines/run", json={"sample_id": sample_id})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"

    # Check if sample status updated
    status_response = client.get(f"/samples/{sample_id}/status")
    assert status_response.json()["status"] == "processing"

def test_get_pipeline_progress():
    from src.api.v1.samples import SAMPLES_DB, PIPELINES_DB
    SAMPLES_DB.clear()
    PIPELINES_DB.clear()

    reg = client.post("/samples/register", json={
        "patient_id": "patient_123",
        "sample_type": "blood",
        "sequencing_type": "WGS"
    })
    sample_id = reg.json()["id"]

    # Updated to send JSON body
    run_response = client.post("/pipelines/run", json={"sample_id": sample_id})
    pipeline_id = run_response.json()["pipeline_id"]

    response = client.get(f"/pipelines/{pipeline_id}/progress")
    assert response.status_code == 200
    assert response.json()["progress"] == "50%"
