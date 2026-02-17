import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import MagicMock
from src.models.audit_models import Chain, AuditStatus, VulnType
from src.api.v1 import contracts

@pytest.fixture
def mock_background_tasks(db_session):
    # Patch AsyncSessionLocal in contracts to use the test session
    mock_session_cls = MagicMock()
    # Mock context manager
    mock_session_cls.return_value.__aenter__.return_value = db_session
    mock_session_cls.return_value.__aexit__.return_value = None

    original = contracts.AsyncSessionLocal
    contracts.AsyncSessionLocal = mock_session_cls
    yield
    contracts.AsyncSessionLocal = original

@pytest.mark.asyncio
async def test_submit_and_audit(client: AsyncClient, db_session, mock_background_tasks):
    # Submit contract with vulnerability
    payload = {
        "chain": Chain.ETHEREUM,
        "source_code": "contract Test { function pay() public payable { (bool success,) = msg.sender.call.value(msg.value)(''); } }",
        "compiler_version": "0.8.0"
    }

    response = await client.post("/api/v1/contracts/submit", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    contract_id = data["id"]

    # Wait for audit to complete (poll)
    for _ in range(20):
        response = await client.get(f"/api/v1/contracts/{contract_id}/audit-status")
        if response.status_code == 200 and response.json()["status"] == AuditStatus.COMPLETED:
            break
        await asyncio.sleep(0.1)

    # Check Report
    response = await client.get(f"/api/v1/contracts/{contract_id}/report")
    assert response.status_code == 200
    report = response.json()
    assert report["status"] == AuditStatus.COMPLETED
    # Depending on mock logic, "call.value" triggers REENTRANCY (CRITICAL)
    assert report["vulnerabilities_found"] > 0
    assert len(report["vulnerabilities"]) > 0

    # Check Vulnerability Details
    vuln_id = report["vulnerabilities"][0]["id"]
    response = await client.get(f"/api/v1/vulnerabilities/{vuln_id}/details")
    assert response.status_code == 200
    assert response.json()["vuln_type"] == VulnType.REENTRANCY

    # Mark False Positive
    response = await client.post(f"/api/v1/vulnerabilities/{vuln_id}/false-positive")
    assert response.status_code == 200

    response = await client.get(f"/api/v1/vulnerabilities/{vuln_id}/details")
    assert response.json()["is_false_positive"] is True

@pytest.mark.asyncio
async def test_search_contracts(client: AsyncClient, mock_background_tasks):
    payload = {
        "chain": Chain.BSC,
        "source_code": "contract Test {}",
        "compiler_version": "0.8.0"
    }
    await client.post("/api/v1/contracts/submit", json=payload)

    response = await client.get("/api/v1/contracts/search?chain=bsc")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["chain"] == Chain.BSC
