import pytest
from httpx import AsyncClient
from src.models.tax_models import EntityType, TaxType, FilingStatus

@pytest.mark.asyncio
async def test_register_entity(client: AsyncClient):
    response = await client.post("/api/v1/entities/register", json={
        "entity_type": "individual",
        "tax_id": "123456789",
        "jurisdiction": "US",
        "fiscal_year_end": "2023-12-31"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["tax_id"] == "123456789"
    assert data["entity_type"] == "individual"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_rule(client: AsyncClient):
    response = await client.post("/api/v1/rules", json={
        "jurisdiction": "US",
        "tax_type": "income",
        "effective_date": "2023-01-01",
        "rate_pct": 0.2,
        "active": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["rate_pct"] == 0.2

@pytest.mark.asyncio
async def test_calculate_tax(client: AsyncClient):
    # First create a rule
    await client.post("/api/v1/rules", json={
        "jurisdiction": "US",
        "tax_type": "income",
        "effective_date": "2023-01-01",
        "rate_pct": 0.25,
        "active": True
    })

    # Register entity
    reg_resp = await client.post("/api/v1/entities/register", json={
        "entity_type": "corporation",
        "tax_id": "987654321",
        "jurisdiction": "US",
        "fiscal_year_end": "2023-12-31"
    })
    entity_id = reg_resp.json()["id"]

    # Calculate
    response = await client.post("/api/v1/filings/calculate", json={
        "entity_id": entity_id,
        "tax_type": "income",
        "period": "2023",
        "gross_income": 100000.0,
        "deductions": {"rent": 20000.0}
    })
    assert response.status_code == 200
    data = response.json()
    # (100000 - 20000) * 0.25 = 20000
    assert data["tax_liability"] == 20000.0

@pytest.mark.asyncio
async def test_calculate_tax_invalid_deduction(client: AsyncClient):
    # Ensure a rule exists so we don't get 404
    await client.post("/api/v1/rules", json={
        "jurisdiction": "US",
        "tax_type": "income",
        "effective_date": "2023-01-01",
        "rate_pct": 0.25,
        "active": True
    })

    # Should fail if deduction is not numeric
    response = await client.post("/api/v1/filings/calculate", json={
        "entity_id": 1,
        "tax_type": "income",
        "period": "2023",
        "gross_income": 100000.0,
        "deductions": {"rent": "not_a_number"}
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_submit_filing(client: AsyncClient):
    # Register entity
    reg_resp = await client.post("/api/v1/entities/register", json={
        "entity_type": "corporation",
        "tax_id": "TAX123",
        "jurisdiction": "UK",
        "fiscal_year_end": "2023-12-31"
    })
    entity_id = reg_resp.json()["id"]

    response = await client.post("/api/v1/filings/submit", json={
        "entity_id": entity_id,
        "tax_type": "vat",
        "period": "2023-Q1",
        "gross_income": 50000.0,
        "tax_liability": 5000.0,
        "due_date": "2023-04-15"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "filed"
    assert data["tax_liability"] == 5000.0 # Verified fix

    # Check status endpoint
    status_resp = await client.get(f"/api/v1/filings/{data['id']}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "filed"
