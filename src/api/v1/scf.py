from fastapi import APIRouter, HTTPException, Query, FastAPI
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum

from src.models.scf_models import InvoiceStatus, OfferStatus, OnboardingStatus

router = APIRouter()

# Pydantic Models

class InvoiceBase(BaseModel):
    supplier_id: int
    buyer_id: int
    invoice_number: str
    amount: float
    currency: str
    issue_date: date
    due_date: date
    discount_rate_pct: Optional[float] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    status: InvoiceStatus

    class Config:
        from_attributes = True

class OfferBase(BaseModel):
    invoice_id: int
    funder_id: int
    advance_rate_pct: float
    interest_rate_annual: float
    offer_amount: float
    tenor_days: int
    status: OfferStatus
    offered_at: datetime

class OfferResponse(OfferBase):
    id: int

    class Config:
        from_attributes = True

class OfferAcceptRequest(BaseModel):
    offer_id: int

class SupplierBase(BaseModel):
    company_name: str
    tax_id: str
    payment_terms_days: Optional[int] = None

class SupplierOnboardRequest(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int
    credit_score: Optional[int] = None
    onboarding_status: OnboardingStatus
    total_financed: float = 0.0

    class Config:
        from_attributes = True

class CreditProfileResponse(BaseModel):
    supplier_id: int
    credit_score: int
    risk_category: str
    limit: float

class EarlyPaymentRequest(BaseModel):
    invoice_id: int
    reason: Optional[str] = None

# Endpoints

@router.get("/invoices", response_model=List[InvoiceResponse])
def get_invoices(
    status: Optional[InvoiceStatus] = None,
    supplier_id: Optional[int] = Query(None, alias="supplier")
):
    # Mock implementation
    return []

@router.post("/invoices/submit", response_model=InvoiceResponse)
def submit_invoice(invoice: InvoiceCreate):
    # Mock implementation
    return {
        "id": 1,
        **invoice.model_dump(),
        "status": InvoiceStatus.submitted
    }

@router.get("/offers/{invoice_id}", response_model=List[OfferResponse])
def get_offers(invoice_id: int):
    # Mock implementation
    return []

@router.post("/offers/accept", response_model=OfferResponse)
def accept_offer(request: OfferAcceptRequest):
    # Mock implementation
    return {
        "id": request.offer_id,
        "invoice_id": 1,
        "funder_id": 1,
        "advance_rate_pct": 80.0,
        "interest_rate_annual": 5.5,
        "offer_amount": 10000.0,
        "tenor_days": 30,
        "status": OfferStatus.accepted,
        "offered_at": datetime.now()
    }

@router.get("/suppliers/{id}/credit-profile", response_model=CreditProfileResponse)
def get_supplier_credit_profile(id: int):
    # Mock implementation
    return {
        "supplier_id": id,
        "credit_score": 750,
        "risk_category": "Low",
        "limit": 50000.0
    }

@router.post("/suppliers/onboard", response_model=SupplierResponse)
def onboard_supplier(supplier: SupplierOnboardRequest):
    # Mock implementation
    return {
        "id": 1,
        **supplier.model_dump(),
        "credit_score": None,
        "onboarding_status": OnboardingStatus.pending,
        "total_financed": 0.0
    }

@router.get("/analytics/dso-trend")
def get_dso_trend(buyer_id: Optional[int] = None):
    # Mock implementation
    return {"buyer_id": buyer_id, "trend": []}

@router.get("/analytics/funding-utilization")
def get_funding_utilization():
    # Mock implementation
    return {"utilization_pct": 45.5, "total_available": 1000000.0}

@router.post("/early-payment/request")
def request_early_payment(request: EarlyPaymentRequest):
    # Mock implementation
    return {"status": "requested", "invoice_id": request.invoice_id}

# Create the app instance for standalone execution
app = FastAPI()
app.include_router(router)
