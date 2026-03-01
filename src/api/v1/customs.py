from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime, timezone
from src.database import get_db
from src.models.customs_models import (
    Declaration, DeclarationType, DeclarationStatus,
    TariffCode, Inspection, InspectionType, InspectionResult
)

router = APIRouter(prefix="/customs", tags=["customs"])

# --- Pydantic Schemas ---

class DeclarationBase(BaseModel):
    reference_number: str
    declaration_type: DeclarationType
    trader_id: str
    country_origin: str
    country_dest: str
    goods: List[dict]
    total_value: float
    currency: str

class DeclarationCreate(DeclarationBase):
    pass

class DeclarationResponse(DeclarationBase):
    id: int
    status: DeclarationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TariffCodeBase(BaseModel):
    hs_code: str
    description: str
    duty_rate_pct: float
    vat_rate_pct: float
    restrictions: List[dict] = []
    preferential_agreements: dict = {}
    effective_date: datetime

class TariffCodeResponse(TariffCodeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class InspectionBase(BaseModel):
    declaration_id: int
    inspection_type: InspectionType
    assigned_officer_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class InspectionCreate(InspectionBase):
    pass

class InspectionResponse(InspectionBase):
    id: int
    result: Optional[InspectionResult]
    findings: Optional[str]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class InspectionResultUpdate(BaseModel):
    result: InspectionResult
    findings: str

class DutyCalculationResponse(BaseModel):
    total_duty: float
    breakdown: dict

# --- Endpoints ---

@router.get("/declarations", response_model=List[DeclarationResponse])
async def get_declarations(
    status: Optional[DeclarationStatus] = None,
    trader_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Declaration)
    if status:
        query = query.where(Declaration.status == status)
    if trader_id:
        query = query.where(Declaration.trader_id == trader_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/declarations/submit", response_model=DeclarationResponse, status_code=status.HTTP_201_CREATED)
async def submit_declaration(declaration: DeclarationCreate, db: AsyncSession = Depends(get_db)):
    db_declaration = Declaration(**declaration.model_dump(), status=DeclarationStatus.SUBMITTED)
    db.add(db_declaration)
    await db.commit()
    await db.refresh(db_declaration)
    return db_declaration

@router.get("/tariffs/lookup", response_model=List[TariffCodeResponse])
async def lookup_tariff(hs_code: str, db: AsyncSession = Depends(get_db)):
    query = select(TariffCode).where(TariffCode.hs_code == hs_code)
    result = await db.execute(query)
    tariffs = result.scalars().all()
    if not tariffs:
        raise HTTPException(status_code=404, detail="Tariff code not found")
    return tariffs

@router.get("/tariffs/calculate-duties", response_model=DutyCalculationResponse)
async def calculate_duties(
    goods: str = Query(..., description="JSON list of goods with 'hs_code' and 'value' keys"),
    db: AsyncSession = Depends(get_db)
):
    try:
        items = json.loads(goods)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for goods")

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Goods must be a list")

    total_duty = 0.0
    breakdown = {}

    for item in items:
        hs_code = item.get("hs_code")
        value = item.get("value")

        if not hs_code or value is None:
            continue

        # Lookup tariff
        query = select(TariffCode).where(TariffCode.hs_code == hs_code)
        result = await db.execute(query)
        tariff = result.scalars().first()

        if tariff:
            item_duty = value * (tariff.duty_rate_pct / 100)
            total_duty += item_duty
            breakdown[hs_code] = item_duty
        else:
            # If not found, assume 0 or handle error. For prototype, 0.
            breakdown[hs_code] = 0.0

    return {
        "total_duty": total_duty,
        "breakdown": breakdown
    }

@router.get("/inspections/queue", response_model=List[InspectionResponse])
async def get_inspection_queue(db: AsyncSession = Depends(get_db)):
    query = select(Inspection).where(Inspection.result == InspectionResult.PENDING).order_by(Inspection.scheduled_at)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/inspections/{id}/result", response_model=InspectionResponse)
async def submit_inspection_result(
    id: int,
    result_update: InspectionResultUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(Inspection).where(Inspection.id == id)
    db_result = await db.execute(query)
    inspection = db_result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    inspection.result = result_update.result
    inspection.findings = result_update.findings
    inspection.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Update declaration status based on inspection result
    declaration_query = select(Declaration).where(Declaration.id == inspection.declaration_id)
    declaration_result = await db.execute(declaration_query)
    declaration = declaration_result.scalar_one_or_none()

    if declaration:
        if result_update.result == InspectionResult.CLEAR:
            declaration.status = DeclarationStatus.CLEARED
        elif result_update.result == InspectionResult.SEIZE:
            declaration.status = DeclarationStatus.REJECTED
        # HOLD might not change status immediately or set to assessing

    await db.commit()
    await db.refresh(inspection)
    return inspection

@router.get("/analytics/clearance-times")
async def get_clearance_times():
    # Mock data
    return {
        "average_hours": 24.5,
        "p95_hours": 48.0,
        "by_port": {"Port A": 22.0, "Port B": 26.5}
    }

@router.get("/compliance/risk-profile/{trader_id}")
async def get_risk_profile(trader_id: str):
    # Mock logic
    return {
        "trader_id": trader_id,
        "risk_level": "low",
        "last_audit": "2023-10-01"
    }

@router.post("/declarations/{id}/appeal")
async def appeal_declaration(id: int):
    return {"message": f"Appeal submitted for declaration {id}"}
