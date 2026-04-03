from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict

from src.database import get_db
from src.models.ehr_models import PatientRecord, LabOrder, ReferralLetter
from src.services.ehr_service import ehr_service
from src.schemas.ehr_schemas import (
    PatientRecordResponse, PatientRecordCreate, LabOrderResponse, LabOrderCreate,
    ReferralResponse, ReferralAccept
)

router = APIRouter(prefix="/ehr", tags=["EHR"])

@router.get("/patients/{patient_id}/record", response_model=PatientRecordResponse)
async def get_patient_record(patient_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(PatientRecord).where(PatientRecord.patient_id == patient_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Patient record not found")

    return record

@router.put("/patients/{patient_id}/record", response_model=PatientRecordResponse)
async def update_patient_record(patient_id: str, record_in: PatientRecordCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(PatientRecord).where(PatientRecord.patient_id == patient_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        record = PatientRecord(patient_id=patient_id)
        db.add(record)

    record.allergies = record_in.allergies
    record.chronic_conditions = record_in.chronic_conditions
    record.medications = record_in.medications
    record.blood_type = record_in.blood_type
    record.emergency_contact = record_in.emergency_contact

    await db.commit()
    await db.refresh(record)
    return record

@router.post("/lab-orders", response_model=LabOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_order(order_in: LabOrderCreate, db: AsyncSession = Depends(get_db)):
    order = LabOrder(**order_in.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order

@router.get("/lab-orders/{order_id}/results", response_model=LabOrderResponse)
async def get_lab_results(order_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(LabOrder).where(LabOrder.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return order

@router.get("/patients/{patient_id}/referrals", response_model=List[ReferralResponse])
async def get_patient_referrals(patient_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ReferralLetter).where(ReferralLetter.patient_id == patient_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/referrals/accept", response_model=ReferralResponse)
async def accept_referral(acceptance: ReferralAccept, db: AsyncSession = Depends(get_db)):
    stmt = select(ReferralLetter).where(ReferralLetter.id == acceptance.referral_id)
    result = await db.execute(stmt)
    referral = result.scalar_one_or_none()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    referral.accepted = acceptance.accepted
    await db.commit()
    await db.refresh(referral)
    return referral
