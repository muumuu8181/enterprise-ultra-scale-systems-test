import pytest
from httpx import AsyncClient
from src.models.clinical_genomics import PopulationStudy, PanelDesign

@pytest.mark.asyncio
async def test_compute_pgx_profile(client: AsyncClient):
    # This will check if it can compute a profile (should succeed with mock data)
    response = await client.get("/patients/123/pgx-profile")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "123"
    assert "cyp2d6_phenotype" in data

@pytest.mark.asyncio
async def test_run_gwas(client: AsyncClient, db_session):
    # Create a dummy study first
    study = PopulationStudy(
        name="Test Study",
        cohort_size=100,
        variants_analyzed=1000
    )
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)

    payload = {"study_id": study.id}
    response = await client.post("/population-studies/gwas", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["study_id"] == study.id
    assert "manhattan_plot_url" in data

@pytest.mark.asyncio
async def test_create_panel_design(client: AsyncClient):
    payload = {
        "name": "Cancer Panel",
        "genes": ["BRCA1", "BRCA2"],
        "disease_indication": "Breast Cancer",
        "coverage_target_pct": 99.5,
        "bait_set_uri": "s3://baits/v1"
    }
    response = await client.post("/panels/design", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cancer Panel"
    assert len(data["genes"]) == 2

@pytest.mark.asyncio
async def test_get_panel_metrics(client: AsyncClient):
    response = await client.get("/panels/1/performance-metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["panel_id"] == 1
    assert "mean_coverage" in data
