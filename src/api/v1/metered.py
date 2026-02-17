from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.services.revenue_service import calculate_mrr

router = APIRouter()

class MeteringEventCreate(BaseModel):
    customer_id: str
    metric: str
    quantity: float
    timestamp: datetime
    idempotency_key: str

class UsageSummary(BaseModel):
    customer_id: str
    period_start: datetime
    period_end: datetime
    total_usage: float

class BillingRecord(BaseModel):
    invoice_id: str
    date: datetime
    amount: float
    status: str

class RetryDunningResponse(BaseModel):
    status: str
    message: str

class CreditRequest(BaseModel):
    customer_id: str
    amount: float
    reason: str

class MRRDashboard(BaseModel):
    current_mrr: float
    currency: str

@router.post("/metering/events", status_code=202)
async def create_metering_event(event: MeteringEventCreate):
    # In a real app, this would push to a queue or DB
    return {"status": "accepted", "idempotency_key": event.idempotency_key}

@router.get("/metering/{customer_id}/usage-summary", response_model=UsageSummary)
async def get_usage_summary(customer_id: str):
    # Dummy response
    return UsageSummary(
        customer_id=customer_id,
        period_start=datetime.now(),
        period_end=datetime.now(),
        total_usage=150.5
    )

@router.get("/customers/{customer_id}/billing-history", response_model=List[BillingRecord])
async def get_billing_history(customer_id: str):
    # Dummy response
    return [
        BillingRecord(invoice_id="inv_123", date=datetime.now(), amount=29.99, status="paid"),
        BillingRecord(invoice_id="inv_124", date=datetime.now(), amount=29.99, status="pending")
    ]

@router.post("/dunning/{invoice_id}/retry", response_model=RetryDunningResponse)
async def retry_dunning(invoice_id: str):
    # Logic to retry payment
    return RetryDunningResponse(status="success", message=f"Retry scheduled for invoice {invoice_id}")

@router.post("/credits/apply")
async def apply_credit(credit: CreditRequest):
    return {"status": "applied", "new_balance": 100.0} # Dummy balance

@router.get("/revenue/mrr-dashboard", response_model=MRRDashboard)
async def get_mrr_dashboard():
    mrr = await calculate_mrr()
    return MRRDashboard(current_mrr=mrr, currency="USD")
