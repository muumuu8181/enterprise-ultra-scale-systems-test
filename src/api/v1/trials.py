from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.db.session import get_db
from src.models.clinical_models import ClinicalTrial, TrialSubject, AdverseEvent
from src.schemas.clinical_schemas import (
    ClinicalTrialCreate, ClinicalTrialRead,
    TrialSubjectEnroll, TrialSubjectRead,
    AdverseEventReport, AdverseEventRead,
    SurvivalResult, ClinicalReport,
    StatisticalAnalysisRequest, StatisticalAnalysisResult
)
from src.services.biostatistics import biostatistics_service

router = APIRouter()

@router.post("/trials/register", response_model=ClinicalTrialRead, status_code=status.HTTP_201_CREATED)
async def register_trial(trial: ClinicalTrialCreate, db: AsyncSession = Depends(get_db)):
    db_trial = ClinicalTrial(**trial.model_dump())
    db.add(db_trial)
    await db.commit()
    await db.refresh(db_trial)
    return db_trial

@router.get("/trials/{id}/enrollment-status", response_model=ClinicalReport)
async def get_enrollment_status(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicalTrial).filter(ClinicalTrial.id == id))
    trial = result.scalars().first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    return await biostatistics_service.generate_clinical_report(id)

@router.post("/trials/{id}/subjects/enroll", response_model=TrialSubjectRead, status_code=status.HTTP_201_CREATED)
async def enroll_subject(id: int, subject: TrialSubjectEnroll, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicalTrial).filter(ClinicalTrial.id == id))
    trial = result.scalars().first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    db_subject = TrialSubject(**subject.model_dump(), trial_id=id)
    db.add(db_subject)
    await db.commit()
    await db.refresh(db_subject)
    return db_subject

@router.post("/subjects/{id}/adverse-event", response_model=AdverseEventRead, status_code=status.HTTP_201_CREATED)
async def report_adverse_event(id: int, event: AdverseEventReport, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrialSubject).filter(TrialSubject.id == id))
    subject = result.scalars().first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    event_data = event.model_dump()
    event_data['subject_id'] = id

    db_event = AdverseEvent(**event_data)
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

@router.get("/trials/{id}/interim-analysis", response_model=SurvivalResult)
async def get_interim_analysis(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicalTrial).filter(ClinicalTrial.id == id))
    trial = result.scalars().first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return await biostatistics_service.run_survival_analysis(id)

@router.post("/trials/{id}/statistical-analysis", response_model=StatisticalAnalysisResult)
async def run_statistical_analysis(id: int, request: StatisticalAnalysisRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicalTrial).filter(ClinicalTrial.id == id))
    trial = result.scalars().first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    sample_size = await biostatistics_service.calculate_sample_size(
        request.effect_size, request.power, request.alpha
    )
    return StatisticalAnalysisResult(required_sample_size=sample_size)
