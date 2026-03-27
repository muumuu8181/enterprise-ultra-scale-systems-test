from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.db.session import get_db
from src.models.treasury_models import TreasuryAsset, GrantApplication, MultisigTransaction, TreasuryHistory, GrantStatus, TransactionType, AssetType

router = APIRouter()

# Schemas

class TreasuryAssetResponse(BaseModel):
    id: int
    dao_id: str
    asset_type: AssetType
    token_address: Optional[str]
    balance: float
    usd_value: float
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

class TreasuryHistoryResponse(BaseModel):
    id: int
    dao_id: str
    asset_id: int
    timestamp: datetime
    balance_before: float
    balance_after: float
    tx_ref: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class Milestone(BaseModel):
    id: int
    description: str
    amount: float
    status: str = "pending"

class GrantApplicationCreate(BaseModel):
    dao_id: str
    applicant_address: str
    requested_amount: float
    description: str
    milestones: List[Milestone]

class GrantApplicationResponse(BaseModel):
    id: int
    dao_id: str
    applicant_address: str
    requested_amount: float
    description: str
    milestones: List[Dict[str, Any]]
    status: GrantStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MultisigTransactionResponse(BaseModel):
    id: int
    dao_id: str
    tx_type: TransactionType
    amount: float
    recipient: str
    signers_required: int
    signatures: List[str]
    executed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MultisigSignRequest(BaseModel):
    signer_address: str
    signature: str

# Endpoints

@router.get("/daos/{dao_id}/treasury", response_model=List[TreasuryAssetResponse])
async def get_treasury(dao_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(TreasuryAsset).where(TreasuryAsset.dao_id == dao_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/daos/{dao_id}/treasury/history", response_model=List[TreasuryHistoryResponse])
async def get_treasury_history(dao_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(TreasuryHistory).where(TreasuryHistory.dao_id == dao_id).order_by(TreasuryHistory.timestamp.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/grants/apply", response_model=GrantApplicationResponse)
async def apply_grant(grant_data: GrantApplicationCreate, db: AsyncSession = Depends(get_db)):
    grant = GrantApplication(
        dao_id=grant_data.dao_id,
        applicant_address=grant_data.applicant_address,
        requested_amount=grant_data.requested_amount,
        description=grant_data.description,
        milestones=[m.model_dump() for m in grant_data.milestones],
        status=GrantStatus.SUBMITTED
    )
    db.add(grant)
    await db.commit()
    await db.refresh(grant)
    return grant

@router.get("/grants/{grant_id}/status", response_model=Dict[str, Any])
async def get_grant_status(grant_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GrantApplication).where(GrantApplication.id == grant_id)
    result = await db.execute(stmt)
    grant = result.scalar_one_or_none()

    if not grant:
        raise HTTPException(status_code=404, detail="Grant application not found")

    return {"status": grant.status, "milestones": grant.milestones}

@router.get("/daos/{dao_id}/multisig/pending", response_model=List[MultisigTransactionResponse])
async def get_pending_multisig(dao_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(MultisigTransaction).where(
        MultisigTransaction.dao_id == dao_id,
        MultisigTransaction.executed == False
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/multisig/{tx_id}/sign", response_model=MultisigTransactionResponse)
async def sign_multisig(tx_id: int, sign_request: MultisigSignRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(MultisigTransaction).where(MultisigTransaction.id == tx_id)
    result = await db.execute(stmt)
    tx = result.scalar_one_or_none()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.executed:
        raise HTTPException(status_code=400, detail="Transaction already executed")

    current_signatures = tx.signatures or []
    if sign_request.signer_address in current_signatures:
         raise HTTPException(status_code=400, detail="Already signed by this address")

    # Append signature (simplified logic, just storing address as signature for now based on prompt saying signatures: JSON)
    # Ideally verify signature here

    updated_signatures = list(current_signatures)
    updated_signatures.append(sign_request.signer_address)
    tx.signatures = updated_signatures

    # Check execution condition
    if len(updated_signatures) >= tx.signers_required:
        tx.executed = True
        # Here we would trigger the actual execution logic

    await db.commit()
    await db.refresh(tx)
    return tx
