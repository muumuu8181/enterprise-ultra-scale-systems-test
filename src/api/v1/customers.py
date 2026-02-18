from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from src.models.telco_models import CustomerType, ServiceType

router = APIRouter()

# --- Pydantic Models ---
class CustomerCreate(BaseModel):
    name: str
    customer_type: CustomerType
    credit_score: Optional[int] = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    customer_type: CustomerType
    account_status: str

class ServiceResponse(BaseModel):
    id: int
    customer_id: int
    service_type: ServiceType
    plan_id: str
    status: str
    activation_date: datetime

class BillResponse(BaseModel):
    customer_id: int
    period: str
    total_amount: float
    breakdown: dict

class PlanChangeRequest(BaseModel):
    service_id: int
    new_plan_id: str

class SuspendRequest(BaseModel):
    reason: Optional[str] = None

class UsageRecord(BaseModel):
    service_id: int
    call_type: str
    duration: int
    bytes: int
    cost: float
    timestamp: datetime

class UsageHistoryResponse(BaseModel):
    customer_id: int
    logs: List[UsageRecord]

# --- Endpoints ---

@router.post("/customers/onboard", response_model=CustomerResponse)
async def onboard_customer(customer: CustomerCreate):
    # Stub implementation
    return CustomerResponse(
        id=1,
        name=customer.name,
        customer_type=customer.customer_type,
        account_status="active"
    )

@router.get("/customers/{customer_id}/services", response_model=List[ServiceResponse])
async def get_customer_services(customer_id: int):
    # Stub implementation
    return [
        ServiceResponse(
            id=101,
            customer_id=customer_id,
            service_type=ServiceType.MOBILE,
            plan_id="plan_basic",
            status="active",
            activation_date=datetime.now(timezone.utc)
        )
    ]

@router.get("/customers/{customer_id}/bill", response_model=BillResponse)
async def get_customer_bill(customer_id: int):
    # Stub implementation
    return BillResponse(
        customer_id=customer_id,
        period="2023-10",
        total_amount=150.50,
        breakdown={"voice": 50.0, "data": 100.50}
    )

@router.post("/customers/{customer_id}/plan-change")
async def change_plan(customer_id: int, request: PlanChangeRequest):
    # Stub implementation
    return {"message": f"Plan for service {request.service_id} changed to {request.new_plan_id}"}

@router.post("/customers/{customer_id}/suspend")
async def suspend_customer(customer_id: int, request: SuspendRequest):
    # Stub implementation
    return {"message": f"Customer {customer_id} suspended. Reason: {request.reason}"}

@router.get("/customers/{customer_id}/usage-history", response_model=UsageHistoryResponse)
async def get_usage_history(customer_id: int):
    # Stub implementation
    return UsageHistoryResponse(
        customer_id=customer_id,
        logs=[
            UsageRecord(
                service_id=101,
                call_type="voice",
                duration=120,
                bytes=0,
                cost=0.50,
                timestamp=datetime.now(timezone.utc)
            )
        ]
    )
