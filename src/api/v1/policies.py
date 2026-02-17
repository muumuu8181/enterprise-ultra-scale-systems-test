from datetime import timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.models.insurance_models import Policy, Claim, Underwriting, PolicyStatus, ClaimStatus, UnderwritingDecision
from src.schemas.insurance import (
    PolicyCreate, PolicyResponse, ClaimCreate, ClaimResponse,
    QuoteRequest, QuoteResponse, UnderwritingResponse
)
from src.services.underwriting_service import calculate_risk_score, auto_underwrite

router = APIRouter()

# Policies Endpoints

@router.post("/policies/quote", response_model=QuoteResponse)
async def get_quote(request: QuoteRequest):
    risk_score = await calculate_risk_score(request.applicant_data)
    # Simple premium calculation based on risk
    base_premium = request.coverage_amount * 0.01
    premium = base_premium * (1 + risk_score)
    return QuoteResponse(premium=premium, risk_score=risk_score)

@router.post("/policies/issue", response_model=PolicyResponse)
async def issue_policy(policy_data: PolicyCreate, db: AsyncSession = Depends(get_db)):
    # Underwriting logic
    full_policy_data = policy_data.model_dump()
    decision = await auto_underwrite(full_policy_data)

    if decision == UnderwritingDecision.REJECTED:
        raise HTTPException(status_code=400, detail="Policy rejected based on underwriting criteria")

    status = PolicyStatus.ACTIVE if decision == UnderwritingDecision.APPROVED else PolicyStatus.PENDING

    applicant_data = policy_data.applicant_data or {}
    risk_score = await calculate_risk_score(applicant_data)

    # Calculate premium
    premium = policy_data.coverage_amount * 0.01 * (1 + risk_score)

    new_policy = Policy(
        holder_id=policy_data.holder_id,
        product_type=policy_data.product_type,
        premium=premium,
        coverage_amount=policy_data.coverage_amount,
        expiry_date=policy_data.expiry_date,
        status=status
    )
    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)

    # Create Underwriting record
    uw = Underwriting(
        policy_id=new_policy.id,
        risk_score=risk_score,
        factors={"reason": "Automatic", "source": "api"},
        decision=decision,
        premium_adjustment=0.0
    )
    db.add(uw)
    await db.commit()

    return new_policy

@router.get("/policies/{id}/schedule", response_model=PolicyResponse)
async def get_policy_schedule(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).filter(Policy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.put("/policies/{id}/renew", response_model=PolicyResponse)
async def renew_policy(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).filter(Policy.id == id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Extend expiry by 1 year
    policy.expiry_date = policy.expiry_date + timedelta(days=365)

    await db.commit()
    await db.refresh(policy)
    return policy

# Claims Endpoints

@router.post("/claims", response_model=ClaimResponse)
async def create_claim(claim_data: ClaimCreate, db: AsyncSession = Depends(get_db)):
    # Verify policy
    result = await db.execute(select(Policy).filter(Policy.id == claim_data.policy_id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    new_claim = Claim(
        policy_id=claim_data.policy_id,
        incident_date=claim_data.incident_date,
        claim_type=claim_data.claim_type,
        claimed_amount=claim_data.claimed_amount,
        status=ClaimStatus.SUBMITTED
    )
    db.add(new_claim)
    await db.commit()
    await db.refresh(new_claim)
    return new_claim

@router.get("/claims/{id}/status", response_model=ClaimResponse)
async def get_claim_status(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).filter(Claim.id == id))
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@router.put("/claims/{id}/approve", response_model=ClaimResponse)
async def approve_claim(id: int, approved_amount: float = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).filter(Claim.id == id))
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.status = ClaimStatus.APPROVED
    claim.approved_amount = approved_amount
    await db.commit()
    await db.refresh(claim)
    return claim
