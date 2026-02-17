import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sanctions_check_matched(client: AsyncClient):
    # Test matched case
    response = await client.get("/api/v1/compliance/sanctions-check/bad_guy")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MATCHED"
    assert data["matched_list"] == "OFAC"

@pytest.mark.asyncio
async def test_sanctions_check_clear(client: AsyncClient):
    # Test clear case
    response = await client.get("/api/v1/compliance/sanctions-check/good_citizen")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CLEAR"
    assert data["matched_list"] is None

@pytest.mark.asyncio
async def test_generate_sar(client: AsyncClient):
    payload = {
        "customer_id": "suspicious_user",
        "transaction_ids": ["tx1", "tx2"]
    }
    response = await client.post("/api/v1/compliance/sar/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "suspicious_user"
    assert len(data["risk_indicators"]) > 0

@pytest.mark.asyncio
async def test_aml_summary(client: AsyncClient):
    response = await client.get("/api/v1/compliance/reports/aml-summary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "risk_score" in data[0]
