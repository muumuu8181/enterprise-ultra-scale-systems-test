from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from src.database import get_db
from src.models.contract_models import (
    Contract, Clause, Amendment,
    ContractType, ContractStatus, ClauseType, RiskLevel, AmendmentStatus
)

router = APIRouter()

# --- Schemas ---

class ContractBase(BaseModel):
    title: str
    contract_type: ContractType
    parties: dict
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    auto_renew: bool = False
    value: float = 0.0
    currency: str = "USD"
    status: ContractStatus = ContractStatus.DRAFT

class ContractCreate(ContractBase):
    pass

class ContractResponse(ContractBase):
    id: int

    class Config:
        from_attributes = True

class ClauseBase(BaseModel):
    contract_id: int
    clause_type: ClauseType
    text: str
    risk_level: RiskLevel
    ai_summary: Optional[str] = None
    negotiable: bool = True

class ClauseCreate(ClauseBase):
    pass

class ClauseResponse(ClauseBase):
    id: int

    class Config:
        from_attributes = True

class AmendmentBase(BaseModel):
    contract_id: int
    amendment_number: int
    changes: dict
    proposed_by: str
    approved_by: Optional[str] = None
    effective_date: datetime
    status: AmendmentStatus = AmendmentStatus.PROPOSED

class AmendmentCreate(AmendmentBase):
    pass

class AmendmentResponse(AmendmentBase):
    id: int

    class Config:
        from_attributes = True

class RiskAnalysisRequest(BaseModel):
    text: str

class RiskAnalysisResponse(BaseModel):
    risk_level: RiskLevel
    summary: str

# --- Endpoints ---

@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts(
    contract_type: Optional[ContractType] = Query(None, alias="type"),
    status: Optional[ContractStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Contract)
    if contract_type:
        query = query.where(Contract.contract_type == contract_type)
    if status:
        query = query.where(Contract.status == status)

    result = await db.execute(query)
    contracts = result.scalars().all()
    return contracts

@router.post("/contracts/create", response_model=ContractResponse)
async def create_contract(
    contract: ContractCreate,
    db: AsyncSession = Depends(get_db)
):
    new_contract = Contract(**contract.model_dump())
    db.add(new_contract)
    await db.commit()
    await db.refresh(new_contract)
    return new_contract

@router.get("/contracts/{id}/clauses", response_model=List[ClauseResponse])
async def list_contract_clauses(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Clause).where(Clause.contract_id == id)
    result = await db.execute(query)
    clauses = result.scalars().all()
    return clauses

@router.post("/clauses/analyze-risk", response_model=RiskAnalysisResponse)
async def analyze_clause_risk(
    request: RiskAnalysisRequest
):
    # Mock AI Analysis
    return RiskAnalysisResponse(
        risk_level=RiskLevel.MEDIUM,
        summary="Automated analysis: This clause contains standard terms but warrants review."
    )

@router.post("/amendments/propose", response_model=AmendmentResponse)
async def propose_amendment(
    amendment: AmendmentCreate,
    db: AsyncSession = Depends(get_db)
):
    new_amendment = Amendment(**amendment.model_dump())
    db.add(new_amendment)
    await db.commit()
    await db.refresh(new_amendment)
    return new_amendment

@router.put("/amendments/{id}/approve", response_model=AmendmentResponse)
async def approve_amendment(
    id: int,
    approved_by: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Amendment).where(Amendment.id == id)
    result = await db.execute(query)
    amendment = result.scalar_one_or_none()

    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")

    amendment.status = AmendmentStatus.APPROVED
    amendment.approved_by = approved_by
    await db.commit()
    await db.refresh(amendment)
    return amendment

@router.get("/contracts/expiring", response_model=List[ContractResponse])
async def get_expiring_contracts(
    days: int = Query(30, description="Days until expiration"),
    db: AsyncSession = Depends(get_db)
):
    expiration_threshold = datetime.utcnow() + timedelta(days=days)
    query = select(Contract).where(
        Contract.expiry_date <= expiration_threshold,
        Contract.expiry_date >= datetime.utcnow(),
        Contract.status == ContractStatus.ACTIVE
    )
    result = await db.execute(query)
    contracts = result.scalars().all()
    return contracts

@router.get("/analytics/contract-value")
async def get_contract_value_analytics(
    db: AsyncSession = Depends(get_db)
):
    query = select(
        Contract.contract_type,
        func.sum(Contract.value).label("total_value"),
        func.count(Contract.id).label("count")
    ).group_by(Contract.contract_type)

    result = await db.execute(query)
    analytics = []
    for row in result:
        analytics.append({
            "contract_type": row.contract_type,
            "total_value": row.total_value,
            "count": row.count
        })
    return analytics

@router.post("/contracts/{id}/generate-pdf")
async def generate_contract_pdf(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Contract).where(Contract.id == id)
    result = await db.execute(query)
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {"message": f"PDF generated for contract {id}", "url": f"/downloads/contract_{id}.pdf"}
