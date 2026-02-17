from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.models.fx_models import FXOrder, FXRate, OrderStatus, OrderType
from src.services.fx_service import FXService

router = APIRouter(prefix="/fx", tags=["Foreign Exchange"])

# --- Pydantic Models ---

class RateResponse(BaseModel):
    id: int
    base_currency: str
    quote_currency: str
    bid: Decimal
    ask: Decimal
    mid: Decimal
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    # Serializer for datetime if needed, but Pydantic handles datetime well.
    # We might need to handle datetime serialization if it returns datetime object.
    # Pydantic v2 handles it.

class ConvertRequest(BaseModel):
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    amount: Decimal = Field(..., gt=0)

class ConvertResponse(BaseModel):
    from_currency: str
    to_currency: str
    amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    timestamp: str

class OrderCreate(BaseModel):
    customer_id: str
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    amount: Decimal = Field(..., gt=0)
    order_type: OrderType
    limit_rate: Optional[Decimal] = Field(None, gt=0)

class OrderResponse(BaseModel):
    id: int
    customer_id: str
    from_currency: str
    to_currency: str
    amount: Decimal
    order_type: OrderType
    limit_rate: Optional[Decimal]
    status: OrderStatus
    executed_rate: Optional[Decimal]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.get("/rates", response_model=List[RateResponse])
async def get_rates(db: AsyncSession = Depends(get_db)):
    """
    現在の為替レート一覧を取得する
    """
    # 全レート取得 (実際は最新のみをフィルタリングすべきだが、ここでは全件返すか、最新のものを取得するロジックが必要)
    # ここではシンプルに最新のものを取得するクエリ例とするが、
    # 実際は通貨ペアごとに最新を取得する。
    # 簡易実装として全件返す。
    query = select(FXRate).limit(100) # Limit to avoid huge dump
    result = await db.execute(query)
    rates = result.scalars().all()
    # Serialize datetime to string explicitly if needed, or let Pydantic handle it.
    # We'll rely on Pydantic's default serialization.
    return rates

@router.post("/convert", response_model=ConvertResponse)
async def convert_currency(request: ConvertRequest, db: AsyncSession = Depends(get_db)):
    """
    通貨換算シミュレーション
    """
    service = FXService(db)
    rate = await service.get_latest_rate(request.from_currency, request.to_currency)

    if not rate:
         raise HTTPException(status_code=404, detail=f"Rate not found for {request.from_currency}/{request.to_currency}")

    # Sell from_currency -> Buy to_currency. Bank buys from customer at BID.
    # Converted amount = amount * bid
    converted_amount = request.amount * rate.bid

    return ConvertResponse(
        from_currency=request.from_currency,
        to_currency=request.to_currency,
        amount=request.amount,
        converted_amount=converted_amount,
        rate=rate.bid,
        timestamp=rate.timestamp.isoformat()
    )

@router.post("/orders", response_model=OrderResponse)
async def place_order(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    注文を配置する (成行/指値)
    """
    service = FXService(db)

    try:
        if order_in.order_type == OrderType.MARKET:
            order = await service.execute_market_order(
                customer_id=order_in.customer_id,
                from_currency=order_in.from_currency,
                to_currency=order_in.to_currency,
                amount=order_in.amount
            )
        elif order_in.order_type == OrderType.LIMIT:
            if order_in.limit_rate is None:
                 raise HTTPException(status_code=400, detail="Limit rate is required for LIMIT orders")

            order = await service.place_limit_order(
                customer_id=order_in.customer_id,
                from_currency=order_in.from_currency,
                to_currency=order_in.to_currency,
                amount=order_in.amount,
                limit_rate=order_in.limit_rate
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid order type")

        return order

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """
    注文状態を取得する
    """
    query = select(FXOrder).where(FXOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
