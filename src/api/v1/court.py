from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
import enum

from src.database import get_db
from src.models.court_models import Case, Hearing, Document, CaseType, CaseStatus, HearingType, HearingStatus, DocType, DocStatus

router = APIRouter()

# Pydantic Schemas

class CaseCreate(BaseModel):
    case_number: str
    case_type: CaseType
    plaintiff: str
    defendant: str
    judge_id: int
    court_id: int

class CaseResponse(CaseCreate):
    id: int
    filed_date: datetime
    status: CaseStatus

    model_config = ConfigDict(from_attributes=True)

class HearingCreate(BaseModel):
    case_id: int
    hearing_type: HearingType
    scheduled_at: datetime
    courtroom: str
    judge_id: int
    duration_min: int

class HearingResponse(HearingCreate):
    id: int
    status: HearingStatus

    model_config = ConfigDict(from_attributes=True)

class DocumentCreate(BaseModel):
    case_id: int
    doc_type: DocType
    filed_by: str
    description: Optional[str] = None
    file_url: str
    sealed: bool = False

class DocumentResponse(DocumentCreate):
    id: int
    filed_at: datetime
    status: DocStatus

    model_config = ConfigDict(from_attributes=True)

class DocketResponse(BaseModel):
    case: CaseResponse
    hearings: List[HearingResponse]
    documents: List[DocumentResponse]

    model_config = ConfigDict(from_attributes=True)

# API Endpoints

@router.get("/cases", response_model=List[CaseResponse])
async def get_cases(
    case_type: Optional[CaseType] = Query(None, alias="type"),
    status: Optional[CaseStatus] = None,
    judge: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Case)
    if case_type:
        query = query.where(Case.case_type == case_type)
    if status:
        query = query.where(Case.status == status)
    if judge:
        query = query.where(Case.judge_id == judge)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/cases/{id}/docket", response_model=DocketResponse)
async def get_case_docket(id: int, db: AsyncSession = Depends(get_db)):
    query = select(Case).options(selectinload(Case.hearings), selectinload(Case.documents)).where(Case.id == id)
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return DocketResponse(
        case=case,
        hearings=case.hearings,
        documents=case.documents
    )

@router.get("/hearings/calendar", response_model=List[HearingResponse])
async def get_hearings_calendar(
    court: Optional[int] = None,
    target_date: Optional[date] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Hearing).join(Case)

    if court:
        query = query.where(Case.court_id == court)
    if target_date:
        # Cast to date for comparison. Note: func.date is PostgreSQL specific usually.
        # SQLite uses strftime or similar. We should be careful with DB compatibility.
        # But user asked for Postgres in docker-compose.
        query = query.where(func.date(Hearing.scheduled_at) == target_date)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/hearings/schedule", response_model=HearingResponse)
async def schedule_hearing(hearing: HearingCreate, db: AsyncSession = Depends(get_db)):
    # Verify case exists
    case = await db.get(Case, hearing.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    new_hearing = Hearing(**hearing.model_dump())
    db.add(new_hearing)
    await db.commit()
    await db.refresh(new_hearing)
    return new_hearing

@router.post("/documents/file", response_model=DocumentResponse)
async def file_document(document: DocumentCreate, db: AsyncSession = Depends(get_db)):
    # Verify case exists
    case = await db.get(Case, document.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    new_doc = Document(**document.model_dump())
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return new_doc

@router.get("/documents/{case_id}/list", response_model=List[DocumentResponse])
async def list_documents(case_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Document).where(Document.case_id == case_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/judges/{id}/caseload")
async def get_judge_caseload(id: int, db: AsyncSession = Depends(get_db)):
    query = select(func.count()).select_from(Case).where(Case.judge_id == id).where(Case.status != CaseStatus.CLOSED)
    result = await db.execute(query)
    count = result.scalar()
    return {"judge_id": id, "active_cases": count}

@router.get("/analytics/case-duration")
async def get_case_duration(case_type: Optional[CaseType] = Query(None, alias="type"), db: AsyncSession = Depends(get_db)):
    # Placeholder implementation
    return {"average_duration_days": 120, "type": case_type if case_type else "all"}

@router.get("/search/precedents")
async def search_precedents(topic: str):
    # Mock search
    return {"topic": topic, "results": ["Precedent A", "Precedent B"]}
