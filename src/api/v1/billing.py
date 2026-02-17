from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from src.models.billing_tenant import BillingCycle, MetricType
from src.services.billing_service import process_stripe_webhook
from pydantic import ConfigDict

# Dependency to verify tenant isolation
async def verify_tenant_access(tenant_id: Optional[str] = None, x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")):
    # Only verify if tenant_id is present in path (it should be for /tenants/{tenant_id}/...)
    # and x_tenant_id header is provided.
    if tenant_id and x_tenant_id and x_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")

router = APIRouter(dependencies=[Depends(verify_tenant_access)])

# Response Models
class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: str
    plan_id: str
    billing_cycle: BillingCycle
    next_billing_date: Optional[datetime] = None
    stripe_sub_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UpgradeRequest(BaseModel):
    plan_id: str
    billing_cycle: BillingCycle

class BillingMethodRequest(BaseModel):
    payment_method_id: str

class InvoiceResponse(BaseModel):
    id: int
    period: str
    total: float
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UsageAlertResponse(BaseModel):
    id: int
    metric: MetricType
    threshold_pct: float
    notified: bool

    model_config = ConfigDict(from_attributes=True)

@router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionResponse)
async def get_subscription(tenant_id: str):
    # Mock response since we don't have a live DB connection here
    return SubscriptionResponse(
        id=1,
        tenant_id=tenant_id,
        plan_id="enterprise",
        billing_cycle=BillingCycle.ANNUAL,
        next_billing_date=datetime.now(timezone.utc),
        stripe_sub_id="sub_mock_123"
    )

@router.post("/tenants/{tenant_id}/upgrade")
async def upgrade_subscription(tenant_id: str, request: UpgradeRequest):
    # Logic to upgrade subscription would go here
    return {"status": "success", "message": f"Upgraded to {request.plan_id}"}

@router.put("/tenants/{tenant_id}/billing-method")
async def update_billing_method(tenant_id: str, request: BillingMethodRequest):
    # Logic to update billing method
    return {"status": "success", "message": "Billing method updated"}

@router.get("/tenants/{tenant_id}/invoices", response_model=List[InvoiceResponse])
async def get_invoices(tenant_id: str):
    # Mock response
    return [
        InvoiceResponse(id=1, period="2023-10", total=1200.0, paid_at=datetime.now(timezone.utc)),
        InvoiceResponse(id=2, period="2023-09", total=1200.0, paid_at=datetime.now(timezone.utc))
    ]

@router.get("/tenants/{tenant_id}/usage-alerts", response_model=List[UsageAlertResponse])
async def get_usage_alerts(tenant_id: str):
    # Mock response
    return [
        UsageAlertResponse(id=1, metric=MetricType.API_CALLS, threshold_pct=80.0, notified=False),
        UsageAlertResponse(id=2, metric=MetricType.STORAGE, threshold_pct=90.0, notified=True)
    ]

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.json()
    result = await process_stripe_webhook(payload)
    return result
