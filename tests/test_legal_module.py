import pytest
from fastapi.testclient import TestClient
from src.api.v1.documents import router
from src.models.legal_models import LegalDocument, Contract, Clause, DocType, RiskLevel

# Create a FastAPI app for testing since we only have a router
from fastapi import FastAPI
app = FastAPI()
app.include_router(router, prefix="/documents")

client = TestClient(app)

def test_legal_document_model():
    doc = LegalDocument(
        id=1,
        doc_type=DocType.CONTRACT,
        title="Test Contract",
        status="draft"
    )
    assert doc.title == "Test Contract"
    assert doc.doc_type == DocType.CONTRACT
    assert doc.status == "draft"

def test_contract_model():
    contract = Contract(
        id=1,
        document_id=1,
        risk_score=85.0
    )
    assert contract.risk_score == 85.0
    assert contract.document_id == 1

def test_clause_model():
    clause = Clause(
        id=1,
        contract_id=1,
        text="Confidentiality...",
        risk_level=RiskLevel.LOW
    )
    assert clause.text == "Confidentiality..."
    assert clause.risk_level == RiskLevel.LOW

def test_upload_document_success():
    files = {'file': ('test.pdf', b'dummy content', 'application/pdf')}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["title"] == "test.pdf"

def test_upload_document_invalid_type():
    files = {'file': ('test.txt', b'dummy content', 'text/plain')}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_get_analysis():
    response = client.get("/documents/1/analysis")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "key_entities" in data

def test_extract_clauses():
    response = client.post("/documents/1/extract-clauses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "clause_type" in data[0]

def test_get_risk_report():
    response = client.get("/documents/1/risk-report")
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert data["contract_id"] == 1

def test_compare_contracts():
    response = client.post("/documents/compare", json={"doc_id_1": 1, "doc_id_2": 2})
    assert response.status_code == 200
    data = response.json()
    assert "differences" in data

def test_search_documents():
    response = client.get("/documents/search?q=NDA")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
