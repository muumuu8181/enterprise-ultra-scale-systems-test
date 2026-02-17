from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from typing import Optional, List, Dict

class Framework(str, Enum):
    BASEL3 = "basel3"
    SOLVENCY2 = "solvency2"

class CapitalResult(BaseModel):
    tier1_capital: float
    rwa: float
    capital_ratio: float
    compliance_status: str

class LimitCheckResult(BaseModel):
    is_approved: bool
    current_exposure: float
    limit: float
    utilization: float

class Trade(BaseModel):
    portfolio_id: str
    counterparty_id: int
    instrument_type: str
    nominal_amount: float
    price: float

class CounterpartyBase(BaseModel):
    name: str
    credit_rating: str
    pd_estimate: float = Field(..., description="Probability of Default")
    lgd_estimate: float = Field(..., description="Loss Given Default")
    ead: float = Field(..., description="Exposure at Default")
    industry: str
    country: str

class CounterpartyCreate(CounterpartyBase):
    pass

class CounterpartyRead(CounterpartyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CreditExposureBase(BaseModel):
    portfolio_id: str
    counterparty_id: int
    exposure_type: str
    nominal: float
    mtm_value: float = Field(..., description="Mark-to-Market Value")
    collateral: float

class CreditExposureCreate(CreditExposureBase):
    pass

class CreditExposureRead(CreditExposureBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RegulatoryCapitalBase(BaseModel):
    entity_id: str
    framework: Framework
    tier1_capital: float
    rwa: float
    capital_ratio: float

class RegulatoryCapitalCreate(RegulatoryCapitalBase):
    pass

class RegulatoryCapitalRead(RegulatoryCapitalBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ExposureReport(BaseModel):
    total_exposure: float
    exposure_by_industry: Dict[str, float]
    exposure_by_country: Dict[str, float]

class ConcentrationReport(BaseModel):
    top_counterparties: List[CounterpartyRead]
    herfindahl_index: float
