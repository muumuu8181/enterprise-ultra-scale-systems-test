from src.models.telco_models import CDRRecord, CallType
from pydantic import BaseModel
from typing import Dict

class Bill(BaseModel):
    customer_id: int
    period: str
    total_amount: float
    breakdown: Dict[str, float]

async def rate_cdr(cdr: CDRRecord) -> float:
    # Simple rating logic
    cost = 0.0

    if cdr.call_type == CallType.VOICE and cdr.duration:
        cost = cdr.duration * 0.01  # $0.01 per second
    elif cdr.call_type == CallType.DATA and cdr.bytes:
        cost = (cdr.bytes / 1024 / 1024) * 0.10  # $0.10 per MB
    elif cdr.call_type == CallType.SMS:
        cost = 0.05  # $0.05 per SMS

    return round(cost, 2)

async def generate_bill(customer_id: int, period: str) -> Bill:
    # Mock bill generation logic
    # In a real system, this would aggregate CDRs for the period
    return Bill(
        customer_id=customer_id,
        period=period,
        total_amount=120.50,
        breakdown={"voice": 20.0, "data": 100.0, "sms": 0.50}
    )

async def calculate_revenue_by_plan(plan_id: str, month: str) -> float:
    # Mock revenue calculation for analytics
    return 75000.0
