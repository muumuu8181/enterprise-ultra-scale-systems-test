import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.models.investigation_aml import AMLCase, CaseStatus
from src.services.investigation_service import visualize_money_flow
from src.api.v1.investigation import router

# Setup Test App
app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_aml_case_model():
    """Test AMLCase model instantiation and defaults."""
    case = AMLCase(
        sar_id="SAR-123",
        analyst_id="AN-001",
        priority=1,
        typology="Structing",
        estimated_proceeds=10000.0,
        disposition="Pending"
    )
    assert case.sar_id == "SAR-123"
    # SQLAlchemy defaults are applied at flush, not instantiation, so status is None here unless set
    assert case.status is None
    assert case.priority == 1

    # Verify the default is configured in metadata
    assert case.__table__.c.status.default.arg == CaseStatus.OPEN

@pytest.mark.asyncio
async def test_investigation_service_visualization():
    """Test service visualization mock return."""
    result = await visualize_money_flow(1)
    assert result.case_id == 1
    assert len(result.nodes) > 0
    assert len(result.edges) > 0

def test_api_open_case():
    """Test POST /cases/open endpoint."""
    payload = {
        "sar_id": "SAR-999",
        "analyst_id": "AN-999",
        "priority": 5,
        "typology": "Layering",
        "estimated_proceeds": 50000.0,
        "description": "Test case"
    }
    response = client.post("/investigation/cases/open", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "open"
    assert "case_id" in data

def test_api_watchlist_search():
    """Test GET /watchlists/search endpoint."""
    # Test positive match
    response = client.get("/investigation/watchlists/search?q=Bad Actor")
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) > 0
    assert data["matches"][0]["name"] == "Bad Actor"

    # Test no match
    response = client.get("/investigation/watchlists/search?q=Good Citizen")
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) == 0
