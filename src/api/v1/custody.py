from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel, Field
from src.database import get_db
from src.models.custody_models import Vault, Transaction, ApprovalPolicy, CustodyType, Blockchain, TxType, TxStatus

router = APIRouter(prefix="/custody", tags=["custody"])

# Pydantic Models
class VaultCreate(BaseModel):
    name: str
    custody_type: CustodyType
    blockchain: Blockchain
    multi_sig_threshold: int = 1
    signers: dict = Field(default_factory=dict)

class TransactionWithdraw(BaseModel):
    vault_id: int
    amount: float
    initiated_by: str

class PolicyUpdate(BaseModel):
    min_approvers: Optional[int] = None
    max_amount_without_approval: Optional[float] = None
    whitelist_addresses: Optional[list] = None
    time_lock_hours: Optional[int] = None
    active: Optional[bool] = None

class VaultResponse(BaseModel):
    id: int
    name: str
    custody_type: CustodyType
    blockchain: Blockchain
    balance: float
    address: str

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    vault_id: int
    tx_type: TxType
    amount: float
    status: TxStatus
    initiated_by: str

    class Config:
        from_attributes = True

class PolicyResponse(BaseModel):
    id: int
    vault_id: int
    min_approvers: int
    active: bool

    class Config:
        from_attributes = True

# Endpoints

@router.get("/vaults", response_model=List[VaultResponse])
async def get_vaults(custody_type: Optional[CustodyType] = Query(None, alias="type"), db: AsyncSession = Depends(get_db)):
    query = select(Vault)
    if custody_type:
        query = query.where(Vault.custody_type == custody_type)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/vaults/create", response_model=VaultResponse)
async def create_vault(vault: VaultCreate, db: AsyncSession = Depends(get_db)):
    # Mock address generation
    import uuid
    new_address = f"0x{uuid.uuid4().hex}"

    db_vault = Vault(
        name=vault.name,
        custody_type=vault.custody_type,
        blockchain=vault.blockchain,
        address=new_address,
        multi_sig_threshold=vault.multi_sig_threshold,
        signers=vault.signers
    )
    db.add(db_vault)
    await db.commit()
    await db.refresh(db_vault)
    return db_vault

@router.post("/transactions/withdraw", response_model=TransactionResponse)
async def withdraw(tx: TransactionWithdraw, db: AsyncSession = Depends(get_db)):
    # Verify vault exists and has balance
    result = await db.execute(select(Vault).where(Vault.id == tx.vault_id))
    vault = result.scalar_one_or_none()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    if vault.balance < tx.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    vault.balance -= tx.amount
    new_tx = Transaction(
        vault_id=tx.vault_id,
        tx_type=TxType.withdrawal,
        amount=tx.amount,
        status=TxStatus.pending,
        initiated_by=tx.initiated_by
    )
    db.add(new_tx)
    await db.commit()
    await db.refresh(new_tx)
    return new_tx

@router.get("/transactions/{id}/status", response_model=dict)
async def get_transaction_status(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction).where(Transaction.id == id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": tx.status}

@router.post("/transactions/{id}/approve")
async def approve_transaction(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction).where(Transaction.id == id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Logic to check policy would go here. For now, we just sign it.
    tx.status = TxStatus.signed
    await db.commit()
    return {"message": "Transaction approved"}

@router.get("/transactions/pending-approvals", response_model=List[TransactionResponse])
async def get_pending_approvals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction).where(Transaction.status == TxStatus.pending))
    return result.scalars().all()

@router.get("/vaults/{id}/balance")
async def get_vault_balance(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vault).where(Vault.id == id))
    vault = result.scalar_one_or_none()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return {"balance": vault.balance, "currency": vault.blockchain}

@router.get("/vaults/{id}/audit-trail", response_model=List[TransactionResponse])
async def get_vault_audit_trail(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction).where(Transaction.vault_id == id))
    return result.scalars().all()

@router.put("/policies/{id}", response_model=PolicyResponse)
async def update_policy(id: int, policy: PolicyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApprovalPolicy).where(ApprovalPolicy.id == id))
    db_policy = result.scalar_one_or_none()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = policy.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_policy, key, value)

    await db.commit()
    await db.refresh(db_policy)
    return db_policy

@router.get("/policies/{vault_id}", response_model=List[PolicyResponse])
async def get_policies(vault_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApprovalPolicy).where(ApprovalPolicy.vault_id == vault_id))
    return result.scalars().all()
