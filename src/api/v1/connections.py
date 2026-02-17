from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.models.openbanking_models import (
    BankConnection, BankAccount, Transaction, ConnectionStatus, AccountType
)
from src.services.plaid_service import PlaidService

router = APIRouter(prefix="/connections", tags=["Open Banking"])
accounts_router = APIRouter(prefix="/accounts", tags=["Open Banking Accounts"])

# --- Pydantic Models ---

class ConnectionInitiateRequest(BaseModel):
    user_id: str
    bank_name: str
    public_token: str # Mocking public token exchange flow

class ConnectionResponse(BaseModel):
    id: int
    user_id: str
    bank_name: str
    status: ConnectionStatus
    expires_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class AccountResponse(BaseModel):
    id: int
    connection_id: int
    account_number_hash: str
    account_type: AccountType
    balance: Decimal
    currency: str
    last_synced: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: Decimal
    currency: str
    merchant: str
    category: Optional[str]
    date: datetime
    description: Optional[str]
    enriched_category: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class BalanceResponse(BaseModel):
    account_id: int
    balance: Decimal
    currency: str
    last_synced: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Connection Endpoints ---

@router.post("/initiate", response_model=ConnectionResponse)
async def initiate_connection(request: ConnectionInitiateRequest, db: AsyncSession = Depends(get_db)):
    """
    Initiate a bank connection (OAuth2 / Plaid Link mock)
    """
    service = PlaidService()

    # Exchange token
    token_data = await service.exchange_token(request.public_token)

    # Create Connection
    connection = BankConnection(
        user_id=request.user_id,
        bank_name=request.bank_name,
        access_token=token_data.access_token,
        status=ConnectionStatus.ACTIVE,
        expires_at=None # Mock no expiration for simplicity
    )

    db.add(connection)
    await db.commit()
    await db.refresh(connection)

    # Mock creating initial accounts for this connection
    acc1 = BankAccount(
        connection_id=connection.id,
        account_number_hash="hash_chk_123",
        account_type=AccountType.CHECKING,
        balance=Decimal("1500.00"),
        currency="USD",
        last_synced=datetime.now(timezone.utc)
    )
    acc2 = BankAccount(
        connection_id=connection.id,
        account_number_hash="hash_sav_456",
        account_type=AccountType.SAVINGS,
        balance=Decimal("5000.00"),
        currency="USD",
        last_synced=datetime.now(timezone.utc)
    )
    db.add_all([acc1, acc2])
    await db.commit()

    return connection

@router.get("/list", response_model=List[ConnectionResponse])
async def list_connections(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    List all active connections for a user
    """
    query = select(BankConnection).where(
        BankConnection.user_id == user_id,
        BankConnection.status != ConnectionStatus.REVOKED
    )
    result = await db.execute(query)
    connections = result.scalars().all()
    return connections

@router.get("/{connection_id}/callback")
async def connection_callback(connection_id: int, db: AsyncSession = Depends(get_db)):
    """
    Callback endpoint for OAuth flow (Mock)
    """
    # Simply verify connection exists
    query = select(BankConnection).where(BankConnection.id == connection_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {"status": "success", "connection_id": connection.id}

@router.delete("/{connection_id}/revoke")
async def revoke_connection(connection_id: int, db: AsyncSession = Depends(get_db)):
    """
    Revoke a bank connection
    """
    query = select(BankConnection).where(BankConnection.id == connection_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.status = ConnectionStatus.REVOKED
    await db.commit()

    return {"status": "revoked"}

# --- Account Endpoints ---

@accounts_router.get("/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    account_id: int,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transactions for an account
    """
    # First verify account exists
    query = select(BankAccount).where(BankAccount.id == account_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Sync new transactions (mock)
    service = PlaidService()

    # Query transactions from DB
    tx_query = select(Transaction).where(Transaction.account_id == account_id)

    if from_date:
        tx_query = tx_query.where(Transaction.date >= from_date)
    if to_date:
        tx_query = tx_query.where(Transaction.date <= to_date)

    tx_result = await db.execute(tx_query)
    transactions = tx_result.scalars().all()

    # If no transactions, sync mock data
    if not transactions:
        # fetch mock transactions
        synced_txs = await service.sync_transactions(account.connection_id)

        for tx_data in synced_txs:
             # Fix account_id to current account for demo
             enriched = await service.categorize_transaction(tx_data)

             tx = Transaction(
                 account_id=account.id,
                 amount=tx_data.amount,
                 currency=tx_data.currency,
                 merchant=tx_data.merchant,
                 category=tx_data.category,
                 date=tx_data.date,
                 description=tx_data.description,
                 enriched_category=enriched
             )
             db.add(tx)

        await db.commit()
        # Re-query
        tx_result = await db.execute(tx_query)
        transactions = tx_result.scalars().all()

    return transactions

@accounts_router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get account balance
    """
    query = select(BankAccount).where(BankAccount.id == account_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return BalanceResponse(
        account_id=account.id,
        balance=account.balance,
        currency=account.currency,
        last_synced=account.last_synced
    )
