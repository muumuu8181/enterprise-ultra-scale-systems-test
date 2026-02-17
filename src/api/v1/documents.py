from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.services.nlp_service import extract_clauses, calculate_risk_score, suggest_revisions

# Mocking database session dependency for now
async def get_db():
    pass

router = APIRouter()

# --- Pydantic Models ---
class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: str
    message: str

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_id: int
    summary: str
    key_entities: List[str]

class ClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    clause_type: str
    text: str
    risk_level: str
    is_standard: bool

class RiskReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    contract_id: int
    risk_score: float
    high_risk_clauses: int

class SearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    results: List[DocumentResponse]

# --- Endpoints ---

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a legal document (PDF/DOCX).
    """
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are supported.")

    # Logic to save file and create DB entry would go here
    return {
        "id": 1,
        "title": file.filename,
        "status": "uploaded",
        "message": "File uploaded successfully"
    }

@router.get("/{id}/analysis", response_model=AnalysisResponse)
async def get_document_analysis(id: int):
    """
    Retrieves initial analysis of the document.
    """
    return {
        "document_id": id,
        "summary": "This is a standard service agreement.",
        "key_entities": ["Company A", "Company B"]
    }

@router.post("/{id}/extract-clauses", response_model=List[ClauseResponse])
async def extract_document_clauses(id: int):
    """
    Triggers clause extraction for the document.
    """
    clauses = await extract_clauses(id)
    # Mapping the dictionary to response model
    return [
        ClauseResponse(
            clause_type=c.clause_type,
            text=c.text,
            risk_level=c.risk_level.value,
            is_standard=c.is_standard
        ) for c in clauses
    ]

@router.get("/{id}/risk-report", response_model=RiskReportResponse)
async def get_risk_report(id: int):
    """
    Generates a risk report for the contract.
    """
    score = await calculate_risk_score(id)
    return {
        "contract_id": id,
        "risk_score": score,
        "high_risk_clauses": 2 # Mock count
    }

@router.post("/compare")
async def compare_contracts(doc_id_1: int = Body(...), doc_id_2: int = Body(...)):
    """
    Compares two contracts and returns differences.
    """
    return {
        "comparison_id": 123,
        "differences": [
            {"clause": "termination", "doc_1": "30 days", "doc_2": "60 days"}
        ]
    }

@router.get("/search", response_model=SearchResponse)
async def search_documents(q: str):
    """
    Searches for documents by query.
    """
    return {
        "results": [
            {"id": 1, "title": "NDA_CompanyA.pdf", "status": "processed", "message": "Found"},
            {"id": 2, "title": "Service_Agreement_v1.docx", "status": "draft", "message": "Found"}
        ]
    }
