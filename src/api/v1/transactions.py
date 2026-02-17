from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ...core.database import get_db
from ...services.account_service import AccountService
from ...services.transaction_service import TransactionService
from ...services.audit_service import AuditService
from ...schemas.transaction import DepositRequest, WithdrawRequest, TransferRequest, TransactionResponse
from ...core.exceptions import AccountNotFound, InsufficientFunds, TransactionFailed

router = APIRouter()

@router.post("/accounts/{account_id}/deposit", response_model=TransactionResponse)
async def deposit(
    account_id: uuid.UUID,
    request: DepositRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """入金"""
    audit = AuditService(db)
    account_service = AccountService(db, audit)
    service = TransactionService(db, audit, account_service)
    try:
        return await service.deposit(account_id, request.amount, request.description or "Deposit", idempotency_key=idempotency_key)
    except (AccountNotFound, TransactionFailed) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/accounts/{account_id}/withdraw", response_model=TransactionResponse)
async def withdraw(
    account_id: uuid.UUID,
    request: WithdrawRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """出金"""
    audit = AuditService(db)
    account_service = AccountService(db, audit)
    service = TransactionService(db, audit, account_service)
    try:
        return await service.withdraw(account_id, request.amount, request.description or "Withdrawal", idempotency_key=idempotency_key)
    except AccountNotFound:
        raise HTTPException(status_code=404, detail="Account not found")
    except InsufficientFunds:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    except TransactionFailed as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfers", response_model=TransactionResponse)
async def transfer(
    request: TransferRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """振込 (2フェーズコミット/ACID)"""
    audit = AuditService(db)
    account_service = AccountService(db, audit)
    service = TransactionService(db, audit, account_service)
    try:
        return await service.transfer(
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            amount=request.amount,
            description=request.description or "Transfer",
            idempotency_key=idempotency_key
        )
    except AccountNotFound:
        raise HTTPException(status_code=404, detail="One or both accounts not found")
    except InsufficientFunds:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    except TransactionFailed as e:
        raise HTTPException(status_code=400, detail=str(e))
