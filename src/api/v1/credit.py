from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.session import get_db
from src.schemas.credit import (
    CounterpartyRead, ExposureReport, CapitalResult,
    RegulatoryCapitalRead, LimitCheckResult, ConcentrationReport,
    Trade
)
from src.services.credit_service import CreditService
from src.models.credit_risk import Counterparty, CreditExposure, RegulatoryCapital

router = APIRouter()

@router.get("/counterparties/{id}/credit-profile", response_model=CounterpartyRead)
async def get_counterparty_profile(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Counterparty).where(Counterparty.id == id))
    counterparty = result.scalar_one_or_none()
    if not counterparty:
        raise HTTPException(status_code=404, detail="Counterparty not found")
    return counterparty

@router.post("/credit/exposure-report", response_model=ExposureReport)
async def create_exposure_report(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CreditExposure, Counterparty)
        .join(Counterparty, CreditExposure.counterparty_id == Counterparty.id)
    )
    rows = result.all()

    total = 0.0
    by_industry = {}
    by_country = {}

    for exposure, counterparty in rows:
        val = exposure.mtm_value
        total += val

        ind = counterparty.industry
        by_industry[ind] = by_industry.get(ind, 0.0) + val

        ctry = counterparty.country
        by_country[ctry] = by_country.get(ctry, 0.0) + val

    return ExposureReport(
        total_exposure=total,
        exposure_by_industry=by_industry,
        exposure_by_country=by_country
    )

@router.post("/regulatory/capital-calculation", response_model=CapitalResult)
async def calculate_capital(
    entity_id: str = Body(...),
    framework: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    service = CreditService(db)
    return await service.compute_regulatory_capital(entity_id, framework)

@router.get("/regulatory/capital-adequacy", response_model=RegulatoryCapitalRead)
async def get_capital_adequacy(
    entity_id: str,
    framework: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RegulatoryCapital).where(
        RegulatoryCapital.entity_id == entity_id,
        RegulatoryCapital.framework == framework
    ))
    cap = result.scalar_one_or_none()
    if not cap:
        raise HTTPException(status_code=404, detail="Capital record not found")
    return cap

@router.post("/credit/limit-check", response_model=LimitCheckResult)
async def check_limit(trade: Trade, db: AsyncSession = Depends(get_db)):
    service = CreditService(db)
    return await service.check_credit_limit(trade)

@router.get("/credit/concentration-report", response_model=ConcentrationReport)
async def get_concentration_report(db: AsyncSession = Depends(get_db)):
    return ConcentrationReport(
        top_counterparties=[],
        herfindahl_index=0.0
    )
