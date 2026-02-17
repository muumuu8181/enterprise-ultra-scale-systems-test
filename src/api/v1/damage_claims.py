from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.rental_models import DamageClaim, Booking
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class DamageClaimCreate(BaseModel):
    description: str
    photos: List[str]

class DamageClaimResolve(BaseModel):
    amount: float
    assessment_notes: Optional[str] = None

class DamageAssessmentResponse(BaseModel):
    id: int
    status: str
    assessment_notes: Optional[str]
    resolved_amount: Optional[float]

@router.post("/{booking_id}")
def create_damage_claim(booking_id: int, claim: DamageClaimCreate, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    new_claim = DamageClaim(
        booking_id=booking_id,
        description=claim.description,
        photos=claim.photos,
        status="pending"
    )
    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)
    return {"status": "submitted", "claim_id": new_claim.id}

@router.get("/{claim_id}/assessment", response_model=DamageAssessmentResponse)
def get_assessment(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(DamageClaim).filter(DamageClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return DamageAssessmentResponse(
        id=claim.id,
        status=claim.status,
        assessment_notes=claim.assessment_notes,
        resolved_amount=claim.resolved_amount
    )

@router.put("/{claim_id}/resolve")
def resolve_claim(claim_id: int, resolve: DamageClaimResolve, db: Session = Depends(get_db)):
    claim = db.query(DamageClaim).filter(DamageClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.status = "resolved"
    claim.resolved_amount = resolve.amount
    if resolve.assessment_notes:
        claim.assessment_notes = resolve.assessment_notes

    db.commit()
    return {"status": "resolved", "amount": resolve.amount}
