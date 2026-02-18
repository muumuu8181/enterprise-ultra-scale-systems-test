from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

from src.models.carbon_models import EmissionSource, CarbonCredit, NetZeroTarget, EmissionSourceType, EmissionScope, CreditStatus
from src.services.carbon_service import CarbonService
from src.database import get_db

router = APIRouter()
carbon_service = CarbonService()

# Pydantic Models
class EmissionReportCreate(BaseModel):
    entity_id: str
    source_type: EmissionSourceType
    scope: EmissionScope
    reported_co2_kt: float

class CarbonCreditRetireRequest(BaseModel):
    credit_id: int
    entity_id: str

class NetZeroPathwayRequest(BaseModel):
    entity_id: str
    baseline_year: int
    target_year: int

class CarbonCreditResponse(BaseModel):
    id: int
    project_id: str
    vintage_year: int
    volume_tco2: float
    status: CreditStatus
    registry: str
    model_config = ConfigDict(from_attributes=True)

# API Endpoints
@router.post("/emissions/report", status_code=status.HTTP_201_CREATED)
async def report_emissions(report: EmissionReportCreate, db: AsyncSession = Depends(get_db)):
    new_emission = EmissionSource(
        entity_id=report.entity_id,
        source_type=report.source_type,
        scope=report.scope,
        reported_co2_kt=report.reported_co2_kt
    )
    db.add(new_emission)
    await db.commit()
    await db.refresh(new_emission)
    return {"message": "Emission report received", "id": new_emission.id}

@router.get("/emissions/entity/{entity_id}/trajectory")
async def get_emission_trajectory(entity_id: str, db: AsyncSession = Depends(get_db)):
    footprint = await carbon_service.calculate_carbon_footprint(db, entity_id, 2023)
    return {
        "entity_id": entity_id,
        "current_footprint_kt": footprint,
        "trajectory": "Stable"
    }

@router.get("/carbon-credits/available", response_model=List[CarbonCreditResponse])
async def get_available_credits(budget: Optional[float] = None, db: AsyncSession = Depends(get_db)):
    if budget:
        credits = await carbon_service.optimize_offset_portfolio(db, budget)
        return credits

    stmt = select(CarbonCredit).where(CarbonCredit.status == CreditStatus.ISSUED)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/carbon-credits/retire")
async def retire_credit(request: CarbonCreditRetireRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(CarbonCredit).where(CarbonCredit.id == request.credit_id)
    result = await db.execute(stmt)
    credit = result.scalar_one_or_none()

    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")

    if credit.status != CreditStatus.ISSUED:
         raise HTTPException(status_code=400, detail="Credit not available for retirement")

    credit.status = CreditStatus.RETIRED
    await db.commit()
    return {"message": f"Credit {request.credit_id} retired for entity {request.entity_id}"}

@router.post("/net-zero/calculate-pathway")
async def calculate_net_zero_pathway(request: NetZeroPathwayRequest, db: AsyncSession = Depends(get_db)):
    roadmap = await carbon_service.generate_netzero_pathway(db, request.entity_id)
    return roadmap

@router.get("/net-zero/global-dashboard")
async def get_global_dashboard(db: AsyncSession = Depends(get_db)):
    return {
        "global_emissions_kt": 50000, # Mock aggregate
        "total_credits_issued": 1200,
        "entities_committed": 15
    }
