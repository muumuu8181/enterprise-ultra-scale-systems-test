from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from src.database import get_db
from src.models.patent_models import Patent, Claim, Citation, PatentStatus, ClaimType, CitationType, Relevance

router = APIRouter()

# --- Schemas ---

class ClaimCreate(BaseModel):
    claim_number: int
    claim_type: ClaimType
    depends_on: Optional[int] = None
    text: str
    scope_keywords: Optional[dict] = None

class PatentCreate(BaseModel):
    patent_number: str
    title: str
    abstract: Optional[str] = None
    inventors: Optional[dict] = None
    assignee_id: Optional[str] = None
    filing_date: Optional[date] = None
    grant_date: Optional[date] = None
    expiry_date: Optional[date] = None
    jurisdiction: Optional[str] = None
    classification: Optional[dict] = None
    status: PatentStatus = PatentStatus.PENDING
    claims: List[ClaimCreate] = []

class ClaimResponse(BaseModel):
    id: int
    patent_id: int
    claim_number: int
    claim_type: ClaimType
    depends_on: Optional[int] = None
    text: str
    scope_keywords: Optional[dict] = None

    class Config:
        from_attributes = True

class CitationResponse(BaseModel):
    id: int
    citing_patent_id: int
    cited_patent_id: int
    citation_type: CitationType
    relevance: Optional[Relevance] = None
    cited_text: Optional[str] = None

    class Config:
        from_attributes = True

class PatentResponse(BaseModel):
    id: int
    patent_number: str
    title: str
    abstract: Optional[str] = None
    inventors: Optional[dict] = None
    assignee_id: Optional[str] = None
    filing_date: Optional[date] = None
    grant_date: Optional[date] = None
    expiry_date: Optional[date] = None
    jurisdiction: Optional[str] = None
    classification: Optional[dict] = None
    status: PatentStatus

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/patents/search", response_model=List[PatentResponse])
def search_patents(
    keyword: Optional[str] = None,
    classification: Optional[str] = Query(None, alias="class"),
    db: Session = Depends(get_db)
):
    query = db.query(Patent)
    if keyword:
        query = query.filter(Patent.title.ilike(f"%{keyword}%") | Patent.abstract.ilike(f"%{keyword}%"))
    if classification:
        # Assuming classification JSON contains a list or specific key.
        # For simplicity, using text cast or specific logic if known.
        # Here we just check if the classification column contains the string.
        # This is a naive implementation for JSON search.
        query = query.filter(Patent.classification.cast(str).ilike(f"%{classification}%"))
    return query.all()

@router.get("/patents/{id}/claims", response_model=List[ClaimResponse])
def get_patent_claims(id: int, db: Session = Depends(get_db)):
    patent = db.query(Patent).filter(Patent.id == id).first()
    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")
    return patent.claims

@router.post("/patents/file", response_model=PatentResponse)
def file_patent(patent_in: PatentCreate, db: Session = Depends(get_db)):
    db_patent = Patent(
        patent_number=patent_in.patent_number,
        title=patent_in.title,
        abstract=patent_in.abstract,
        inventors=patent_in.inventors,
        assignee_id=patent_in.assignee_id,
        filing_date=patent_in.filing_date,
        grant_date=patent_in.grant_date,
        expiry_date=patent_in.expiry_date,
        jurisdiction=patent_in.jurisdiction,
        classification=patent_in.classification,
        status=patent_in.status
    )
    db.add(db_patent)
    db.commit()
    db.refresh(db_patent)

    for claim_in in patent_in.claims:
        db_claim = Claim(
            patent_id=db_patent.id,
            claim_number=claim_in.claim_number,
            claim_type=claim_in.claim_type,
            depends_on=claim_in.depends_on,
            text=claim_in.text,
            scope_keywords=claim_in.scope_keywords
        )
        db.add(db_claim)

    db.commit()
    return db_patent

@router.get("/patents/{id}/status")
def get_patent_status(id: int, db: Session = Depends(get_db)):
    patent = db.query(Patent).filter(Patent.id == id).first()
    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")
    return {"status": patent.status}

@router.get("/citations/{patent_id}/forward", response_model=List[CitationResponse])
def get_forward_citations(patent_id: int, db: Session = Depends(get_db)):
    # Patents that cite this patent
    citations = db.query(Citation).filter(Citation.cited_patent_id == patent_id).all()
    return citations

@router.get("/citations/{patent_id}/backward", response_model=List[CitationResponse])
def get_backward_citations(patent_id: int, db: Session = Depends(get_db)):
    # Patents that this patent cites
    citations = db.query(Citation).filter(Citation.citing_patent_id == patent_id).all()
    return citations

@router.get("/analytics/landscape")
def get_landscape_analytics(technology: str, db: Session = Depends(get_db)):
    # Mock analytics: Count patents by status for a given technology (keyword search)
    # Technology keyword search in title/abstract/classification
    query = db.query(Patent.status, func.count(Patent.id)).filter(
        (Patent.title.ilike(f"%{technology}%")) |
        (Patent.abstract.ilike(f"%{technology}%"))
    ).group_by(Patent.status)
    results = query.all()
    return [{"status": status, "count": count} for status, count in results]

@router.get("/analytics/competitor/{assignee_id}")
def get_competitor_analytics(assignee_id: str, db: Session = Depends(get_db)):
    # Mock analytics: Count patents by status for a specific assignee
    query = db.query(Patent.status, func.count(Patent.id)).filter(
        Patent.assignee_id == assignee_id
    ).group_by(Patent.status)
    results = query.all()
    return [{"status": status, "count": count} for status, count in results]

@router.post("/patents/{id}/maintain-fees")
def maintain_patent_fees(id: int, db: Session = Depends(get_db)):
    # Mock logic: verify patent exists and return success
    patent = db.query(Patent).filter(Patent.id == id).first()
    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")

    # Logic to record fee payment would go here
    return {"message": "Fees maintenance recorded", "patent_id": id}
