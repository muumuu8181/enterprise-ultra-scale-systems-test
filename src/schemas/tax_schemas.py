from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from src.models.tax_models import EntityType, TaxType, FilingStatus

class TaxEntityBase(BaseModel):
    entity_type: EntityType
    tax_id: str
    jurisdiction: str
    fiscal_year_end: date
    filing_status: Optional[str] = "active"

class TaxEntityCreate(TaxEntityBase):
    pass

class TaxEntityResponse(TaxEntityBase):
    id: int
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaxFilingBase(BaseModel):
    entity_id: int
    tax_type: TaxType
    period: str
    gross_income: float = 0.0
    deductions: Dict[str, Any] = {}
    due_date: date

class TaxFilingCreate(TaxFilingBase):
    tax_liability: float = 0.0

class TaxFilingUpdate(BaseModel):
    gross_income: Optional[float] = None
    deductions: Optional[Dict[str, Any]] = None
    tax_liability: Optional[float] = None
    status: Optional[FilingStatus] = None
    due_date: Optional[date] = None

class TaxFilingResponse(TaxFilingBase):
    id: int
    tax_liability: float
    status: FilingStatus
    model_config = ConfigDict(from_attributes=True)

class TaxRuleBase(BaseModel):
    jurisdiction: str
    tax_type: TaxType
    effective_date: date
    rate_pct: float
    brackets: Optional[List[Dict[str, Any]]] = None
    exemptions: Optional[Dict[str, Any]] = None
    active: bool = True

class TaxRuleCreate(TaxRuleBase):
    pass

class TaxRuleResponse(TaxRuleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CalculationRequest(BaseModel):
    entity_id: int
    tax_type: TaxType
    period: str
    gross_income: float
    deductions: Dict[str, Any] = {}

class CalculationResponse(BaseModel):
    tax_liability: float
    details: Dict[str, Any]
