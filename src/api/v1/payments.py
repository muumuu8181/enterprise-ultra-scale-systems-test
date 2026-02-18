from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from src.models.payment_models import Transaction, Refund

router = APIRouter()

# Pydantic Models
class ChargeRequest(BaseModel):
    amount: float
    currency: str
    method_id: int
    idempotency_key: str

class RefundRequest(BaseModel):
    amount: float
    reason: str

class TransactionResponse(BaseModel):
    id: int
    payer_id: str
    payee_id: str
    amount: float
    currency: str
    method_id: int
    status: str
    idempotency_key: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RefundResponse(BaseModel):
    id: int
    transaction_id: int
    amount: float
    reason: str
    status: str
    initiated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.post("/payments/charge", response_model=TransactionResponse)
async def create_charge(request: ChargeRequest):
    """
    支払いを実行する
    """
    # Logic placeholder
    # 実際のアプリケーションではここでデータベースへの保存や決済ゲートウェイとの通信を行います

    return TransactionResponse(
        id=1,
        payer_id="user_123",
        payee_id="merchant_456",
        amount=request.amount,
        currency=request.currency,
        method_id=request.method_id,
        status="COMPLETED",
        idempotency_key=request.idempotency_key,
        created_at=datetime.now(timezone.utc)
    )

@router.get("/payments/{id}", response_model=TransactionResponse)
async def get_payment(id: int):
    """
    支払詳細を取得する
    """
    # Logic placeholder
    if id == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse(
        id=id,
        payer_id="user_123",
        payee_id="merchant_456",
        amount=1000.0,
        currency="JPY",
        method_id=1,
        status="COMPLETED",
        idempotency_key="mock_key",
        created_at=datetime.now(timezone.utc)
    )

@router.post("/payments/{id}/refund", response_model=RefundResponse)
async def refund_payment(id: int, request: RefundRequest):
    """
    返金を実行する
    """
    # Logic placeholder
    return RefundResponse(
        id=1,
        transaction_id=id,
        amount=request.amount,
        reason=request.reason,
        status="COMPLETED",
        initiated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
