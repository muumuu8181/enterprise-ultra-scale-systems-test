from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

from src.database import get_db
from src.models.museum_models import (
    Artifact, Exhibition, LoanAgreement, ConservationLog,
    ArtifactCondition, ExhibitionStatus, LoanStatus
)

router = APIRouter()

# --- Schemas ---

class ArtifactBase(BaseModel):
    accession_number: str
    title: str
    artist_creator: str
    period: str
    medium: str
    dimensions: str
    provenance: List[dict] = []
    location_gallery: str
    condition: ArtifactCondition
    insurance_value: float

class ArtifactCreate(ArtifactBase):
    pass

class ArtifactResponse(ArtifactBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ExhibitionBase(BaseModel):
    title: str
    curator_id: int
    theme: str
    start_date: date
    end_date: date
    galleries: List[str] = []
    artifact_ids: List[int] = []
    status: ExhibitionStatus = ExhibitionStatus.PLANNING

class ExhibitionCreate(ExhibitionBase):
    pass

class ExhibitionResponse(ExhibitionBase):
    id: int
    visitor_count: int
    model_config = ConfigDict(from_attributes=True)

class LoanRequest(BaseModel):
    artifact_id: int
    borrower_institution: str
    purpose: str
    loan_start: date
    loan_end: date
    insurance_amount: float

class LoanResponse(LoanRequest):
    id: int
    status: LoanStatus
    condition_report_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ConservationReportCreate(BaseModel):
    artifact_id: int
    log_date: date
    description: str
    reporter: str
    new_condition: Optional[ArtifactCondition] = None

class ConservationLogResponse(BaseModel):
    id: int
    artifact_id: int
    log_date: date
    description: str
    reporter: str
    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.post("/artifacts", response_model=ArtifactResponse)
async def create_artifact(artifact: ArtifactCreate, db: AsyncSession = Depends(get_db)):
    db_artifact = Artifact(**artifact.model_dump())
    db.add(db_artifact)
    await db.commit()
    await db.refresh(db_artifact)
    return db_artifact

@router.get("/artifacts", response_model=List[ArtifactResponse])
async def get_artifacts(
    period: Optional[str] = Query(None),
    medium: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Artifact)
    if period:
        query = query.where(Artifact.period == period)
    if medium:
        query = query.where(Artifact.medium == medium)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/artifacts/{id}/provenance")
async def get_artifact_provenance(id: int, db: AsyncSession = Depends(get_db)):
    artifact = await db.get(Artifact, id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.provenance

@router.get("/exhibitions", response_model=List[ExhibitionResponse])
async def get_exhibitions(
    status: Optional[ExhibitionStatus] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Exhibition)
    if status:
        query = query.where(Exhibition.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/exhibitions/create", response_model=ExhibitionResponse)
async def create_exhibition(exhibition: ExhibitionCreate, db: AsyncSession = Depends(get_db)):
    db_exhibition = Exhibition(**exhibition.model_dump())
    db.add(db_exhibition)
    await db.commit()
    await db.refresh(db_exhibition)
    return db_exhibition

@router.post("/loans/request", response_model=LoanResponse)
async def request_loan(loan: LoanRequest, db: AsyncSession = Depends(get_db)):
    # Check if artifact exists
    artifact = await db.get(Artifact, loan.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    db_loan = LoanAgreement(
        **loan.model_dump(),
        status=LoanStatus.REQUESTED
    )
    db.add(db_loan)
    await db.commit()
    await db.refresh(db_loan)
    return db_loan

@router.get("/loans/active", response_model=List[LoanResponse])
async def get_active_loans(db: AsyncSession = Depends(get_db)):
    query = select(LoanAgreement).where(LoanAgreement.status == LoanStatus.ACTIVE)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/conservation/{artifact_id}/condition-log", response_model=List[ConservationLogResponse])
async def get_condition_log(artifact_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ConservationLog).where(ConservationLog.artifact_id == artifact_id).order_by(ConservationLog.log_date)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/conservation/report", response_model=ConservationLogResponse)
async def create_conservation_report(report: ConservationReportCreate, db: AsyncSession = Depends(get_db)):
    artifact = await db.get(Artifact, report.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    db_log = ConservationLog(
        artifact_id=report.artifact_id,
        log_date=report.log_date,
        description=report.description,
        reporter=report.reporter
    )
    db.add(db_log)

    if report.new_condition:
        artifact.condition = report.new_condition
        db.add(artifact) # Mark as modified

    await db.commit()
    await db.refresh(db_log)
    return db_log

@router.get("/analytics/popular-exhibits", response_model=List[ExhibitionResponse])
async def get_popular_exhibits(db: AsyncSession = Depends(get_db)):
    query = select(Exhibition).order_by(desc(Exhibition.visitor_count))
    result = await db.execute(query)
    return result.scalars().all()
