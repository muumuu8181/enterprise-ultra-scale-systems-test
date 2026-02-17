from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

from src.db.session import get_db
from src.services.risk_engine import RiskEngine, SimResult, StressResult
from src.models.risk_models import Portfolio, RiskMetric, Position

router = APIRouter()

class RiskMetricResponse(BaseModel):
    portfolio_id: int
    var_95: float
    var_99: float
    cvar_95: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float

    model_config = ConfigDict(from_attributes=True)

class VarRequest(BaseModel):
    confidence: float = 0.95
    horizon: int = 1

class StressTestRequest(BaseModel):
    scenario: Dict[str, float]

class ExposureResponse(BaseModel):
    portfolio_id: int
    asset_allocation: Dict[str, float]

class ScenarioRunRequest(BaseModel):
    portfolio_id: int
    simulations: int = 1000

@router.get("/portfolios/{portfolio_id}/risk-metrics", response_model=List[RiskMetricResponse])
async def get_risk_metrics(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskMetric).where(RiskMetric.portfolio_id == portfolio_id))
    metrics = result.scalars().all()
    # If empty list, return empty list
    return metrics

@router.post("/portfolios/{portfolio_id}/var-calculate")
async def calculate_var_endpoint(
    portfolio_id: int,
    request: VarRequest,
    db: AsyncSession = Depends(get_db)
):
    engine = RiskEngine(db)
    try:
        var = await engine.calculate_var(portfolio_id, request.confidence, request.horizon)
        return {"portfolio_id": portfolio_id, "var": var, "confidence": request.confidence, "horizon": request.horizon}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/portfolios/{portfolio_id}/stress-test", response_model=StressResult)
async def stress_test_endpoint(
    portfolio_id: int,
    request: StressTestRequest,
    db: AsyncSession = Depends(get_db)
):
    engine = RiskEngine(db)
    try:
        result = await engine.stress_test(portfolio_id, request.scenario)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/portfolios/{portfolio_id}/exposures", response_model=ExposureResponse)
async def get_exposures(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    # Calculate exposure by asset type
    engine = RiskEngine(db)
    try:
        # Fetch positions manually to avoid async loading issues without explicit query
        # or use awaitable_attrs if configured
        portfolio = await engine._get_portfolio(portfolio_id)

        # Load positions
        result = await db.execute(select(Position).where(Position.portfolio_id == portfolio_id))
        positions = result.scalars().all()

        allocation = {}
        total_value = portfolio.total_value
        if total_value == 0:
            return ExposureResponse(portfolio_id=portfolio_id, asset_allocation={})

        for pos in positions:
            atype = pos.asset_type.value # Enum
            current_alloc = allocation.get(atype, 0.0)
            allocation[atype] = current_alloc + pos.current_value

        # Normalize
        for k in allocation:
            allocation[k] = allocation[k] / total_value

        return ExposureResponse(
            portfolio_id=portfolio_id,
            asset_allocation=allocation
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/scenarios/run", response_model=SimResult)
async def run_scenario(
    request: ScenarioRunRequest,
    db: AsyncSession = Depends(get_db)
):
    engine = RiskEngine(db)
    try:
        result = await engine.run_monte_carlo(request.portfolio_id, request.simulations)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/market-data/correlation-matrix")
async def get_correlation_matrix():
    # Return a mock correlation matrix
    return {
        "assets": ["AAPL", "GOOG", "MSFT"],
        "matrix": [
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.4],
            [0.3, 0.4, 1.0]
        ]
    }
