import pytest
from src.services.risk_engine import RiskEngine
from src.models.risk_models import Portfolio, Position, PortfolioType, AssetType

@pytest.mark.asyncio
async def test_risk_calculations(db_session):
    # Setup
    p = Portfolio(
        owner_id=1,
        portfolio_type=PortfolioType.EQUITY,
        total_value=100000.0,
        currency="USD"
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    pos = Position(
        portfolio_id=p.id,
        asset_id="AAPL",
        asset_type=AssetType.STOCK,
        quantity=100,
        avg_cost=150.0,
        current_value=16000.0
    )
    db_session.add(pos)
    await db_session.commit()

    engine = RiskEngine(db_session)

    # Test VaR
    var = await engine.calculate_var(p.id, confidence=0.95, horizon_days=1)
    # 100k * 1.645 * (0.20/sqrt(252)) * sqrt(1) approx 2072
    assert var > 0
    assert var < 5000 # Rough check

    # Test Stress Test
    res = await engine.stress_test(p.id, {"market_shock": -0.20})
    assert res.loss_percentage == 20.0
    assert res.stressed_value == 80000.0

    # Test Monte Carlo
    mc_res = await engine.run_monte_carlo(p.id, simulations=100)
    assert mc_res.simulations == 100
    assert mc_res.mean_value > 0
