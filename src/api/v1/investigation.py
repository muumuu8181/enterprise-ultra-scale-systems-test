from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from src.core.database import get_db
from src.models.investigation import (
    FraudCase, InvestigationNote, Chargeback,
    FraudCaseType, FraudCaseStatus, ChargebackStatus
)
from src.services.investigation_service import InvestigationService

router = APIRouter()
service = InvestigationService()

# Pydantic Models
class FraudCaseCreate(BaseModel):
    transaction_ids: List[str]
    case_type: FraudCaseType
    estimated_loss: float

class FraudCaseResponse(BaseModel):
    id: int
    transaction_ids: List[str]
    case_type: FraudCaseType
    status: FraudCaseStatus
    estimated_loss: float
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class NoteCreate(BaseModel):
    investigator_id: str
    note: str
    evidence: Optional[dict] = None
    action_taken: Optional[str] = None

class NoteResponse(BaseModel):
    id: int
    case_id: int
    investigator_id: str
    note: str
    evidence: Optional[dict] = None
    action_taken: Optional[str] = None
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ChargebackCreate(BaseModel):
    transaction_id: str
    reason_code: str
    dispute_amount: float

class ChargebackResponse(BaseModel):
    id: int
    transaction_id: str
    reason_code: str
    dispute_amount: float
    status: ChargebackStatus
    bank_response: Optional[str] = None
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.post("/cases/open", response_model=FraudCaseResponse)
async def open_case(case_in: FraudCaseCreate, db: AsyncSession = Depends(get_db)):
    new_case = FraudCase(
        transaction_ids=case_in.transaction_ids,
        case_type=case_in.case_type,
        estimated_loss=case_in.estimated_loss,
        status=FraudCaseStatus.OPEN
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    return new_case

@router.get("/cases/{id}/timeline", response_model=List[NoteResponse])
async def get_case_timeline(id: int, db: AsyncSession = Depends(get_db)):
    # Simple implementation: return notes as timeline
    result = await db.execute(select(InvestigationNote).where(InvestigationNote.case_id == id))
    notes = result.scalars().all()
    return notes

@router.post("/cases/{id}/notes")
async def add_case_note(id: int, note_in: NoteCreate, db: AsyncSession = Depends(get_db)):
    # Verify case exists
    result = await db.execute(select(FraudCase).where(FraudCase.id == id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    new_note = InvestigationNote(
        case_id=id,
        investigator_id=note_in.investigator_id,
        note=note_in.note,
        evidence=note_in.evidence,
        action_taken=note_in.action_taken
    )
    db.add(new_note)
    await db.commit()
    return {"status": "Note added"}

@router.post("/cases/{id}/close")
async def close_case(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FraudCase).where(FraudCase.id == id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = FraudCaseStatus.CLOSED
    await db.commit()
    return {"status": "Case closed"}

@router.post("/chargebacks/record", response_model=ChargebackResponse)
async def record_chargeback(cb_in: ChargebackCreate, db: AsyncSession = Depends(get_db)):
    new_cb = Chargeback(
        transaction_id=cb_in.transaction_id,
        reason_code=cb_in.reason_code,
        dispute_amount=cb_in.dispute_amount,
        status=ChargebackStatus.RECEIVED
    )
    db.add(new_cb)
    await db.commit()
    await db.refresh(new_cb)
    return new_cb

@router.get("/chargebacks/{id}/respond")
async def respond_to_chargeback(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chargeback).where(Chargeback.id == id))
    cb = result.scalar_one_or_none()
    if not cb:
        raise HTTPException(status_code=404, detail="Chargeback not found")

    # Logic to determine response (mock)
    return {"recommendation": "Accept Liability", "evidence_required": ["proof_of_delivery"]}

@router.get("/analytics/fraud-losses")
async def get_fraud_losses(period: str = Query("month", pattern="^(month|quarter|year)$")):
    loss_rate = await service.calculate_fraud_loss_rate(period)
    return {"period": period, "fraud_loss_rate": loss_rate}
