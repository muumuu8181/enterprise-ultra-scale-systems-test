from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Pydantic models
class SubscriberCreate(BaseModel):
    msisdn: str
    plan_id: int
    imsi: str
    sim_type: str

class SubscriberResponse(BaseModel):
    id: int
    msisdn: str
    status: Optional[str] = None
    plan_id: int
    imsi: str
    sim_type: str

class PlanUpdate(BaseModel):
    plan_id: int

class TopUpRequest(BaseModel):
    amount: float

class UsageResponse(BaseModel):
    subscriber_id: int
    usage: List[dict]

class BillResponse(BaseModel):
    subscriber_id: int
    bills: List[dict]

@router.post("/subscribers", response_model=SubscriberResponse)
async def create_subscriber(subscriber: SubscriberCreate):
    # Mock implementation
    return SubscriberResponse(
        id=1,
        msisdn=subscriber.msisdn,
        status="active",
        plan_id=subscriber.plan_id,
        imsi=subscriber.imsi,
        sim_type=subscriber.sim_type
    )

@router.get("/subscribers/{id}/usage", response_model=UsageResponse)
async def get_usage(id: int):
    return {"subscriber_id": id, "usage": []}

@router.put("/subscribers/{id}/plan")
async def update_plan(id: int, plan: PlanUpdate):
    return {"message": "Plan updated successfully"}

@router.post("/subscribers/{id}/top-up")
async def top_up(id: int, top_up: TopUpRequest):
    return {"message": f"Top up of {top_up.amount} successful"}

@router.get("/subscribers/{id}/bills", response_model=BillResponse)
async def get_bills(id: int):
    return {"subscriber_id": id, "bills": []}
