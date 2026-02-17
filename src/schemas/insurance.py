from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from src.models.insurance_models import ProductType, PolicyStatus, ClaimStatus, UnderwritingDecision

class PolicyBase(BaseModel):
    holder_id: int
    product_type: ProductType
    coverage_amount: float
    expiry_date: datetime

class PolicyCreate(PolicyBase):
    applicant_data: Optional[Dict[str, Any]] = None

class PolicyResponse(PolicyBase):
    id: int
    premium: float
    status: PolicyStatus

    model_config = ConfigDict(from_attributes=True)

class ClaimBase(BaseModel):
    policy_id: int
    incident_date: datetime
    claim_type: str
    claimed_amount: float

class ClaimCreate(ClaimBase):
    pass

class ClaimResponse(ClaimBase):
    id: int
    approved_amount: Optional[float] = None
    status: ClaimStatus

    model_config = ConfigDict(from_attributes=True)

class UnderwritingResponse(BaseModel):
    id: int
    policy_id: int
    risk_score: float
    factors: Dict[str, Any]
    decision: UnderwritingDecision
    premium_adjustment: float

    model_config = ConfigDict(from_attributes=True)

class QuoteRequest(BaseModel):
    applicant_data: Dict[str, Any]
    product_type: ProductType
    coverage_amount: float

class QuoteResponse(BaseModel):
    premium: float
    risk_score: float
