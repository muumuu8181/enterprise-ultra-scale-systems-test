from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from ...core.database import get_db
from ...services.account_service import AccountService
from ...services.transaction_service import TransactionService
from ...services.audit_service import AuditService
from ...schemas.account import AccountCreate, AccountResponse
from ...schemas.transaction import TransactionEntryResponse
from ...core.exceptions import AccountNotFound, CustomerNotFound

router = APIRouter()

def get_services(db: AsyncSession = Depends(get_db)):
    audit = AuditService(db)
    account = AccountService(db, audit)
    transaction = TransactionService(db, audit, account)
    return account, transaction

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: AccountCreate,
    db: AsyncSession = Depends(get_db)
):
    """口座開設"""
    audit = AuditService(db)
    service = AccountService(db, audit)
    try:
        return await service.create_account(
            customer_id=account_in.customer_id,
            account_type=account_in.account_type,
            currency=account_in.currency
        )
    except CustomerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """口座照会"""
    audit = AuditService(db)
    service = AccountService(db, audit)
    try:
        return await service.get_account(account_id)
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{account_id}/transactions", response_model=List[TransactionEntryResponse])
async def get_transactions(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """取引履歴照会"""
    audit = AuditService(db)
    account_service = AccountService(db, audit)
    service = TransactionService(db, audit, account_service)
    try:
        return await service.get_transactions(account_id)
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
