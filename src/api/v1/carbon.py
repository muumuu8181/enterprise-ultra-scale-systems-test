from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from src.models.carbon_models import Standard, CreditType, ProjectType, CreditStatus, TradeStatus

# Dummy dependency
def get_db():
    yield None

router = APIRouter(prefix="/carbon", tags=["carbon"])

# Pydantic Models
class CarbonProjectBase(BaseModel):
    name: str
    country: str
    methodology: str
    project_type: ProjectType
    annual_credits: int
    registry_url: Optional[str] = None

class CarbonProjectCreate(CarbonProjectBase):
    pass

class CarbonProjectResponse(CarbonProjectBase):
    id: int
    verification_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CarbonCreditBase(BaseModel):
    project_id: int
    vintage_year: int
    standard: Standard
    credit_type: CreditType
    tonnes_co2: float
    serial_number: str
    owner_id: str

class CarbonCreditCreate(CarbonCreditBase):
    pass

class CarbonCreditResponse(CarbonCreditBase):
    id: int
    status: CreditStatus

    model_config = ConfigDict(from_attributes=True)

class TradeOrderBase(BaseModel):
    buyer_id: Optional[str] = None
    seller_id: str
    credit_id: int
    quantity: float
    price_per_tonne: float
    currency: str = "USD"

class TradeOrderCreate(TradeOrderBase):
    pass

class TradeOrderResponse(TradeOrderBase):
    id: int
    status: TradeStatus
    traded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class OffsetSummary(BaseModel):
    owner_id: str
    total_credits: float
    retired_credits: float
    active_credits: float

# Endpoints

@router.get("/credits", response_model=List[CarbonCreditResponse])
def get_credits(
    standard: Optional[Standard] = Query(None),
    vintage: Optional[int] = Query(None),
    db = Depends(get_db)
):
    return []

@router.post("/credits/issue", response_model=CarbonCreditResponse)
def issue_credit(credit: CarbonCreditCreate, db = Depends(get_db)):
    return CarbonCreditResponse(id=1, status=CreditStatus.ISSUED, **credit.model_dump())

@router.get("/projects/{id}", response_model=CarbonProjectResponse)
def get_project(id: int, db = Depends(get_db)):
    return CarbonProjectResponse(
        id=id,
        name="Test Project",
        country="US",
        methodology="VM0001",
        project_type=ProjectType.FORESTRY,
        annual_credits=1000,
        verification_date=datetime.now()
    )

@router.post("/projects/register", response_model=CarbonProjectResponse)
def register_project(project: CarbonProjectCreate, db = Depends(get_db)):
    return CarbonProjectResponse(id=1, verification_date=datetime.now(), **project.model_dump())

@router.post("/trades/order", response_model=TradeOrderResponse)
def create_trade_order(order: TradeOrderCreate, db = Depends(get_db)):
    return TradeOrderResponse(id=1, status=TradeStatus.PENDING, **order.model_dump())

@router.get("/trades/orderbook", response_model=List[TradeOrderResponse])
def get_orderbook(db = Depends(get_db)):
    return []

@router.get("/portfolio/{owner_id}/offset-summary", response_model=OffsetSummary)
def get_offset_summary(owner_id: str, db = Depends(get_db)):
    return OffsetSummary(
        owner_id=owner_id,
        total_credits=100.0,
        retired_credits=20.0,
        active_credits=80.0
    )

@router.post("/credits/{id}/retire", response_model=CarbonCreditResponse)
def retire_credit(id: int, db = Depends(get_db)):
    return CarbonCreditResponse(
        id=id,
        project_id=1,
        vintage_year=2023,
        standard=Standard.VERRA,
        credit_type=CreditType.AVOIDANCE,
        tonnes_co2=10.0,
        serial_number="TEST-123",
        owner_id="owner1",
        status=CreditStatus.RETIRED
    )
