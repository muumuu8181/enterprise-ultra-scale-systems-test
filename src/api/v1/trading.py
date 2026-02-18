from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from src.services.market_service import clear_market, calculate_clearing_price
from src.models.energy_models import BidStatus

router = APIRouter()

# Pydantic Models for API
class BidRequest(BaseModel):
    generator_id: int
    volume_mwh: float
    min_price: float
    max_price: float
    delivery_period: str

class BidResponse(BidRequest):
    id: int
    status: str

class TradeResponse(BaseModel):
    id: int
    buyer_id: str
    seller_id: str
    volume_mwh: float
    price_per_mwh: float
    delivery_start: str
    delivery_end: str
    trade_type: str

# In-memory storage for demonstration
bids_store = {}
trades_store = {}

@router.post("/bids/submit", response_model=BidResponse)
async def submit_bid(bid: BidRequest):
    bid_id = len(bids_store) + 1
    new_bid = {
        "id": bid_id,
        **bid.model_dump(),
        "status": BidStatus.pending.value
    }
    bids_store[bid_id] = new_bid
    return new_bid

@router.get("/bids/{id}/status")
async def get_bid_status(id: int):
    if id not in bids_store:
        raise HTTPException(status_code=404, detail="Bid not found")
    return {"id": id, "status": bids_store[id]["status"]}

@router.get("/market/orderbook")
async def get_orderbook(period: str = "2h"):
    # Return all bids currently in store
    return list(bids_store.values())

@router.get("/market/clearing-price")
async def get_clearing_price():
    # Convert stored bids to format expected by service (list of objects/dicts with price)
    # We use max_price as the bid price for calculation
    current_bids = [{"price": b["max_price"]} for b in bids_store.values()]
    # Mock asks
    current_asks = [{"price": 50.0}, {"price": 60.0}]

    price = await calculate_clearing_price(current_bids, current_asks)
    return {"clearing_price": price}

@router.post("/trades/execute")
async def execute_trades():
    trades = await clear_market("current")
    return {"executed_trades": trades}

@router.get("/trades/{id}/settlement")
async def get_trade_settlement(id: int):
    # Mock implementation
    return {
        "trade_id": id,
        "settlement_amount": 1500.0, # Mock amount
        "currency": "USD",
        "status": "settled"
    }
