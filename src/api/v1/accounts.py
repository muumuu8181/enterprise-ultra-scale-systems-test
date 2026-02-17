from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from src.database import AsyncSessionLocal
from src.models.finance_models import Account, Transaction, AccountType as ModelAccountType
from src.schemas.finance_schemas import (
    ConnectAccountRequest,
    ManualAccountRequest,
    CategorizeTransactionRequest,
    TransactionResponse
)
from src.services.finance_service import auto_categorize

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/accounts/connect")
async def connect_account(request: ConnectAccountRequest, db: AsyncSession = Depends(get_db)):
    # Using ModelAccountType(request.account_type.value) to convert from Pydantic Enum to SQLAlchemy Enum
    new_account = Account(
        user_id=request.user_id,
        institution=request.institution,
        account_name=request.account_name,
        account_type=ModelAccountType(request.account_type.value),
        balance=0.0
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return {"message": "Account connected", "account_id": new_account.id}

@router.get("/accounts/{id}/balance")
async def get_balance(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).filter(Account.id == id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account.id, "balance": account.balance, "currency": account.currency}

@router.get("/accounts/{id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    id: int,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).filter(Transaction.account_id == id)
    if from_date:
        query = query.filter(Transaction.date >= from_date)
    if to_date:
        query = query.filter(Transaction.date <= to_date)

    result = await db.execute(query)
    transactions = result.scalars().all()
    return transactions

@router.post("/accounts/manual")
async def manual_account_entry(request: ManualAccountRequest, db: AsyncSession = Depends(get_db)):
    new_account = Account(
        user_id=request.user_id,
        account_name=request.account_name,
        account_type=ModelAccountType(request.account_type.value),
        balance=request.balance,
        currency=request.currency,
        institution="Manual"
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return {"message": "Account created manually", "account_id": new_account.id}

@router.post("/transactions/categorize")
async def categorize_transaction(request: CategorizeTransactionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Transaction).filter(Transaction.id == request.transaction_id))
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    category = await auto_categorize(transaction)
    transaction.category = category
    await db.commit()
    return {"transaction_id": transaction.id, "category": category}

@router.get("/transactions/export")
async def export_transactions(user_id: int, db: AsyncSession = Depends(get_db)):
    # Export logic (e.g., CSV generation)
    result = await db.execute(select(Transaction).join(Account).filter(Account.user_id == user_id))
    transactions = result.scalars().all()
    return {"count": len(transactions), "data": transactions}
