from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import date
from src.database import get_db
from src.models.tax_models import TaxEntity, TaxFiling, TaxRule, EntityType, TaxType, FilingStatus
from src.schemas.tax_schemas import (
    TaxEntityCreate, TaxEntityResponse,
    TaxFilingCreate, TaxFilingResponse, TaxFilingUpdate,
    TaxRuleCreate, TaxRuleResponse,
    CalculationRequest, CalculationResponse
)

router = APIRouter(tags=["Tax Compliance"])

# Entity Endpoints
@router.post("/entities/register", response_model=TaxEntityResponse)
async def register_entity(entity: TaxEntityCreate, db: AsyncSession = Depends(get_db)):
    db_entity = TaxEntity(**entity.model_dump())
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    return db_entity

@router.get("/entities/{id}/obligations")
async def get_entity_obligations(id: int, db: AsyncSession = Depends(get_db)):
    entity = await db.get(TaxEntity, id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Logic: Find active rules for this entity's jurisdiction and check if filings exist for current periods
    stmt = select(TaxRule).where(
        TaxRule.jurisdiction == entity.jurisdiction,
        TaxRule.active == True
    )
    result = await db.execute(stmt)
    rules = result.scalars().all()

    obligations = []
    for rule in rules:
        obligations.append({
            "tax_type": rule.tax_type,
            "due_date": "2023-12-31", # Simplified logic
            "description": f"{rule.tax_type} filing for {rule.jurisdiction}"
        })
    return obligations

# Filing Endpoints
@router.post("/filings/calculate", response_model=CalculationResponse)
async def calculate_tax(request: CalculationRequest, db: AsyncSession = Depends(get_db)):
    # Fetch applicable rules
    stmt = select(TaxRule).where(
        TaxRule.tax_type == request.tax_type,
        TaxRule.active == True
    )
    result = await db.execute(stmt)
    rules = result.scalars().all()

    if not rules:
        raise HTTPException(status_code=404, detail="No applicable tax rules found")

    # Simple calculation logic (highest rate found)
    rate = 0.0
    for rule in rules:
        if rule.rate_pct > rate:
            rate = rule.rate_pct

    deduction_sum = 0.0
    if request.deductions:
        for key, value in request.deductions.items():
            if not isinstance(value, (int, float)):
                 raise HTTPException(status_code=400, detail=f"Invalid deduction value for {key}: must be numeric")
            deduction_sum += value

    tax_liability = (request.gross_income - deduction_sum) * rate

    return CalculationResponse(
        tax_liability=tax_liability,
        details={"rate_applied": rate, "rules_count": len(rules)}
    )

@router.post("/filings/submit", response_model=TaxFilingResponse)
async def submit_filing(filing: TaxFilingCreate, db: AsyncSession = Depends(get_db)):
    # Calculate liability first? Or assume it's passed?
    # Here we create the filing record.
    db_filing = TaxFiling(**filing.model_dump())
    db_filing.status = FilingStatus.FILED
    db.add(db_filing)
    await db.commit()
    await db.refresh(db_filing)
    return db_filing

@router.get("/filings/{id}/status")
async def get_filing_status(id: int, db: AsyncSession = Depends(get_db)):
    filing = await db.get(TaxFiling, id)
    if not filing:
        raise HTTPException(status_code=404, detail="Filing not found")
    return {"status": filing.status}

@router.get("/filings/upcoming-deadlines")
async def get_upcoming_deadlines(db: AsyncSession = Depends(get_db)):
    stmt = select(TaxFiling).where(
        TaxFiling.due_date >= date.today(),
        TaxFiling.status != FilingStatus.ACCEPTED
    ).order_by(TaxFiling.due_date)
    result = await db.execute(stmt)
    filings = result.scalars().all()
    return filings

@router.post("/filings/{id}/amend", response_model=TaxFilingResponse)
async def amend_filing(id: int, update_data: TaxFilingUpdate, db: AsyncSession = Depends(get_db)):
    filing = await db.get(TaxFiling, id)
    if not filing:
        raise HTTPException(status_code=404, detail="Filing not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(filing, key, value)

    filing.status = FilingStatus.AMENDED
    await db.commit()
    await db.refresh(filing)
    return filing

# Rules & Analytics
@router.get("/rules", response_model=List[TaxRuleResponse])
async def get_rules(
    jurisdiction: Optional[str] = None,
    tax_type: Optional[TaxType] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(TaxRule)
    if jurisdiction:
        stmt = stmt.where(TaxRule.jurisdiction == jurisdiction)
    if tax_type:
        stmt = stmt.where(TaxRule.tax_type == tax_type)

    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/rules", response_model=TaxRuleResponse)
async def create_rule(rule: TaxRuleCreate, db: AsyncSession = Depends(get_db)):
    db_rule = TaxRule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@router.get("/analytics/tax-burden/{entity_id}")
async def get_tax_burden(entity_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(func.sum(TaxFiling.tax_liability)).where(
        TaxFiling.entity_id == entity_id,
        TaxFiling.status.in_([FilingStatus.FILED, FilingStatus.ACCEPTED])
    )
    result = await db.execute(stmt)
    total_burden = result.scalar() or 0.0
    return {"entity_id": entity_id, "total_tax_burden": total_burden}
