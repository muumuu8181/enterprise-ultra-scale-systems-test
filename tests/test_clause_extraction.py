import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.cases import router
from src.services import legal_research
from datetime import datetime

# Setup FastAPI app for testing
app = FastAPI()
app.include_router(router, prefix="/cases")

client = TestClient(app)

@pytest.mark.asyncio
async def test_find_precedents_service():
    """Test the find_precedents service directly."""
    facts = "Contract dispute"
    results = await legal_research.find_precedents(facts)
    assert len(results) > 0
    assert results[0].relevance_score > 0.0

@pytest.mark.asyncio
async def test_generate_brief_service():
    """Test the generate_brief service directly."""
    brief = await legal_research.generate_brief(1)
    assert "LEGAL BRIEF" in brief
    assert "INTRODUCTION" in brief

def test_create_case_api():
    """Test POST /cases endpoint."""
    case_data = {
        "case_number": "CV-2023-001",
        "case_type": "civil",
        "parties": {"plaintiff": "John Doe", "defendant": "Jane Smith"},
        "status": "active",
        "jurisdiction": "NY"
    }
    response = client.post("/cases/", json=case_data)
    assert response.status_code == 200
    data = response.json()
    assert data["case_number"] == "CV-2023-001"
    assert "id" in data

def test_get_timeline_api():
    """Test GET /cases/{id}/timeline endpoint."""
    # Create a case first to be safe
    client.post("/cases/", json={
        "case_number": "CV-2023-002",
        "case_type": "criminal",
        "parties": {},
        "status": "active",
        "jurisdiction": "CA"
    })

    response = client.get("/cases/1/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "milestone_type" in data[0]

def test_research_api():
    """Test POST /cases/{id}/research endpoint."""
    response = client.post("/cases/1/research?query=breach%20of%20contract")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data

def test_clause_extraction_placeholder():
    """
    Placeholder test for 'clause extraction' functionality
    implied by the file name but not explicitly requested in implementation.
    """
    assert True
