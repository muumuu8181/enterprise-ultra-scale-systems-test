import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_recommend_reservations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/optimization/reserved-instances/recommendations", params={"account_id": "123"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "provider" in data[0]

@pytest.mark.asyncio
async def test_purchase_reservation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "provider": "AWS",
            "instance_type": "m5.large",
            "region": "us-east-1",
            "term_months": 12,
            "upfront_cost": 1200.0,
            "monthly_savings": 50.0,
            "estimated_utilization_pct": 85.0
        }
        response = await ac.post("/api/v1/optimization/reserved-instances/purchase", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_tagging_compliance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/optimization/tagging-compliance/123")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "compliance_score" in data
    assert "non_compliant_resources" in data

@pytest.mark.asyncio
async def test_enforce_tagging():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/optimization/tagging/enforce", json={"account_id": "123"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["account_id"] == "123"
    assert "enforced_actions" in data

@pytest.mark.asyncio
async def test_carbon_report():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Note: params passed as query string, json as body
        response = await ac.post("/api/v1/optimization/carbon/report", params={"period": "month"}, json={"account_id": "123"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["account_id"] == "123"
    assert "co2e_tonnes" in data

@pytest.mark.asyncio
async def test_reduction_roadmap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/optimization/carbon/reduction-roadmap")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "steps" in data
    assert isinstance(data["steps"], list)
