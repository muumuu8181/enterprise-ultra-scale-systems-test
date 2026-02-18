from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone

from src.models.subscription_models import Subscription, Plan, UsageRecord, Invoice, ProrationResult, SubscriptionStatus, UsageMetric
from src.services.billing_service import BillingService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
usage_router = APIRouter(prefix="/usage", tags=["usage"])

# Placeholder for DB dependency
async def get_db():
    # Placeholder: In a real app, this would yield a session from a sessionmaker
    # Raising NotImplementedError ensures developers know this needs configuration
    raise NotImplementedError("Database session dependency not configured. Please override get_db.")

async def get_billing_service(db: AsyncSession = Depends(get_db)) -> BillingService:
    return BillingService(db)

class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: int

class SubscriptionUpgrade(BaseModel):
    new_plan_id: int

class UsageRecordCreate(BaseModel):
    subscription_id: int
    metric: UsageMetric
    quantity: float

@router.post("/create", response_model=Dict[str, Any])
async def create_subscription(
    sub_in: SubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    # Fetch plan to get trial days
    plan = await db.get(Plan, sub_in.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    from datetime import timedelta
    trial_end = datetime.now(timezone.utc) + timedelta(days=plan.trial_days)

    new_sub = Subscription(
        customer_id=sub_in.customer_id,
        plan_id=sub_in.plan_id,
        status=SubscriptionStatus.TRIALING,
        current_period_end=trial_end
    )
    db.add(new_sub)
    await db.commit()
    await db.refresh(new_sub)
    return {"id": new_sub.id, "status": new_sub.status}

@router.get("/{id}/status")
async def get_subscription_status(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    sub = await db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"status": sub.status}

@router.post("/{id}/upgrade", response_model=ProrationResult)
async def upgrade_subscription(
    id: int,
    upgrade_in: SubscriptionUpgrade,
    service: BillingService = Depends(get_billing_service)
):
    return await service.apply_proration(id, upgrade_in.new_plan_id)

@router.post("/{id}/cancel")
async def cancel_subscription(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    sub = await db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.status = SubscriptionStatus.CANCELLED
    await db.commit()
    return {"status": "cancelled"}

@router.get("/{id}/upcoming-invoice", response_model=Invoice)
async def get_upcoming_invoice(
    id: int,
    service: BillingService = Depends(get_billing_service)
):
    return await service.generate_invoice(id)

@usage_router.post("/record")
async def record_usage(
    record_in: UsageRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify sub exists
    sub = await db.get(Subscription, record_in.subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    usage = UsageRecord(
        subscription_id=record_in.subscription_id,
        metric=record_in.metric,
        quantity=record_in.quantity,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(usage)
    await db.commit()
    return {"status": "recorded"}
