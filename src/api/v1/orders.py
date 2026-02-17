from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from src.models.trading_models import Order, OrderResult, TradingAccount, Position
import src.services.order_service as order_service

router = APIRouter()

@router.post("/orders/place", response_model=OrderResult)
async def place_order(order: Order):
    result = await order_service.place_order(order.account_id, order)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result

@router.get("/orders/{id}/status")
async def get_order_status(id: str):
    order = order_service.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"id": order.id, "status": order.status}

@router.delete("/orders/{id}/cancel")
async def cancel_order(id: str):
    success = order_service.cancel_order(id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not cancel order")
    return {"message": "Order cancelled"}

@router.get("/orders/history", response_model=List[Order])
async def get_order_history():
    return order_service.get_order_history()

@router.get("/positions/{account_id}", response_model=List[Position])
async def get_positions(account_id: str):
    return order_service.get_positions(account_id)

@router.get("/portfolio/{account_id}/summary")
async def get_portfolio_summary(account_id: str):
    account = order_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    portfolio_value = await order_service.calculate_portfolio_value(account_id)

    return {
        "account_id": account.id,
        "balance": account.balance,
        "buying_power": account.buying_power,
        "portfolio_value": portfolio_value
    }
