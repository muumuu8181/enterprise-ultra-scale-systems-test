from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.database import get_db
from src.models.pricing_models import Product, PricingRule, PriceChange, RuleType, PriceChangeReason
from src.tasks import optimize_price

router = APIRouter()

# Schemas
class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    base_cost: float
    current_price: float
    model_config = ConfigDict(from_attributes=True)

class RuleCreate(BaseModel):
    product_id: int
    rule_type: RuleType
    conditions: dict
    min_price: float
    max_price: float
    priority: int
    model_config = ConfigDict(from_attributes=True)

class RepriceRequest(BaseModel):
    new_price: float
    reason: PriceChangeReason

class OptimizationSimulation(BaseModel):
    category: str
    strategy: str

class BulkRepriceRequest(BaseModel):
    product_ids: List[int]
    percentage_change: float

class PriceChangeResponse(BaseModel):
    id: int
    product_id: int
    old_price: float
    new_price: float
    reason: PriceChangeReason
    effective_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PricingRuleResponse(BaseModel):
    id: int
    product_id: int
    rule_type: RuleType
    conditions: dict
    min_price: float
    max_price: float
    priority: int
    active: bool
    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.get("/products/{id}/price-history", response_model=List[PriceChangeResponse])
async def get_price_history(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceChange).where(PriceChange.product_id == id))
    history = result.scalars().all()
    return history

@router.post("/products/{id}/reprice")
async def reprice_product(id: int, request: RepriceRequest, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    change = PriceChange(
        product_id=id,
        old_price=product.current_price,
        new_price=request.new_price,
        reason=request.reason
    )
    product.current_price = request.new_price
    db.add(change)
    await db.commit()
    return {"status": "repriced", "new_price": request.new_price}

@router.get("/rules")
async def get_rules(category: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(PricingRule)
    if category:
        query = query.join(Product).where(Product.category == category)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/rules/create", response_model=PricingRuleResponse)
async def create_rule(rule: RuleCreate, db: AsyncSession = Depends(get_db)):
    new_rule = PricingRule(**rule.model_dump())
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule

@router.get("/optimization/recommendations")
async def get_recommendations(category: Optional[str] = None):
    return {"recommendations": [{"product_id": 1, "suggested_price": 19.99, "confidence": 0.95}]}

@router.post("/optimization/simulate")
async def simulate_optimization(sim: OptimizationSimulation):
    return {"impact_forecast": {"revenue": "+5%", "margin": "+2%"}}

@router.get("/competitors/price-index")
async def get_competitor_price_index():
    return {"market_index": 1.05, "competitors": {"amazon": 1.02, "walmart": 0.98}}

@router.get("/analytics/margin-impact")
async def get_margin_impact():
    return {"current_margin": 0.25, "projected_margin": 0.28}

@router.post("/bulk-reprice")
async def bulk_reprice(request: BulkRepriceRequest, background_tasks: BackgroundTasks):
    task = optimize_price.delay(request.product_ids, request.percentage_change)
    return {"status": "queued", "job_id": str(task.id)}
