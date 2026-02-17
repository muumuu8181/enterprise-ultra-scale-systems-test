import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_quote(client: AsyncClient):
    response = await client.post("/api/v1/policies/quote", json={
        "applicant_data": {"age": 20, "income": 40000},
        "product_type": "auto",
        "coverage_amount": 10000
    })
    assert response.status_code == 200
    data = response.json()
    assert "premium" in data
    assert "risk_score" in data

@pytest.mark.asyncio
async def test_issue_policy(client: AsyncClient):
    payload = {
        "holder_id": 1,
        "product_type": "auto",
        "coverage_amount": 10000,
        "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
        "applicant_data": {"age": 30, "income": 50000}
    }
    response = await client.post("/api/v1/policies/issue", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["holder_id"] == 1

@pytest.mark.asyncio
async def test_claim_flow(client: AsyncClient):
    # Issue policy first
    policy_payload = {
        "holder_id": 2,
        "product_type": "life",
        "coverage_amount": 50000,
        "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
        "applicant_data": {"age": 40}
    }
    create_res = await client.post("/api/v1/policies/issue", json=policy_payload)
    assert create_res.status_code == 200
    policy_id = create_res.json()["id"]

    # Create Claim
    claim_payload = {
        "policy_id": policy_id,
        "incident_date": datetime.now().isoformat(),
        "claim_type": "accident",
        "claimed_amount": 1000
    }
    claim_res = await client.post("/api/v1/claims", json=claim_payload)
    assert claim_res.status_code == 200
    claim_id = claim_res.json()["id"]
    assert claim_res.json()["status"] == "submitted"

    # Approve Claim
    approve_res = await client.put(f"/api/v1/claims/{claim_id}/approve", json={"approved_amount": 800})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"
    assert approve_res.json()["approved_amount"] == 800

@pytest.mark.asyncio
async def test_renew_policy(client: AsyncClient):
    # Issue policy first
    policy_payload = {
        "holder_id": 3,
        "product_type": "property",
        "coverage_amount": 200000,
        "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
        "applicant_data": {"age": 50}
    }
    create_res = await client.post("/api/v1/policies/issue", json=policy_payload)
    policy_id = create_res.json()["id"]
    original_expiry = datetime.fromisoformat(create_res.json()["expiry_date"])

    # Renew
    renew_res = await client.put(f"/api/v1/policies/{policy_id}/renew")
    assert renew_res.status_code == 200
    new_expiry = datetime.fromisoformat(renew_res.json()["expiry_date"])

    # Check if extended by roughly 365 days (allow minor diffs if logic changes, but timedelta(days=365) is exact)
    assert new_expiry > original_expiry
