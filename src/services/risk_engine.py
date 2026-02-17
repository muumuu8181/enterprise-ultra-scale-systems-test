import numpy as np
from scipy.stats import norm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from src.models.risk_models import Portfolio, Position, RiskMetric

class SimResult(BaseModel):
    portfolio_id: int
    simulations: int
    mean_value: float
    median_value: float
    worst_case_99: float
    best_case_99: float
    simulation_paths: Optional[List[List[float]]] = None # Optional to save bandwidth

class StressResult(BaseModel):
    portfolio_id: int
    scenario_name: str
    original_value: float
    stressed_value: float
    loss_amount: float
    loss_percentage: float

class RiskEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_portfolio(self, portfolio_id: int) -> Portfolio:
        result = await self.db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
        portfolio = result.scalars().first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        return portfolio

    async def calculate_var(self, portfolio_id: int, confidence: float = 0.95, horizon_days: int = 1) -> float:
        """
        Calculates Parametric VaR.
        Assumption: Annual volatility is fixed at 20% for demonstration.
        """
        portfolio = await self._get_portfolio(portfolio_id)

        # In a real system, we would fetch historical prices for assets in the portfolio
        # and calculate the covariance matrix.
        # Here, we simplify: VaR = Value * Z * Vol * sqrt(t)

        annual_volatility = 0.20 # 20%
        daily_volatility = annual_volatility / np.sqrt(252)
        horizon_volatility = daily_volatility * np.sqrt(horizon_days)

        z_score = norm.ppf(confidence)

        # VaR is typically expressed as a positive loss number
        var = portfolio.total_value * z_score * horizon_volatility
        return float(var)

    async def run_monte_carlo(self, portfolio_id: int, simulations: int = 10000, horizon_days: int = 252) -> SimResult:
        """
        Runs Monte Carlo simulation for portfolio value.
        """
        portfolio = await self._get_portfolio(portfolio_id)
        current_value = portfolio.total_value

        # Simulation parameters
        mu = 0.08 / 252 # 8% annual return
        sigma = 0.20 / np.sqrt(252) # 20% annual volatility
        dt = 1 # 1 day steps

        # Simulate paths: S_t = S_0 * exp((mu - 0.5*sigma^2)*t + sigma*W_t)
        # We just want the final distribution for now

        # Random component: N(0, 1) * sqrt(T)
        # Using numpy for vectorization
        brownian_motion = np.random.normal(0, np.sqrt(horizon_days), simulations)

        # Drift and Diffusion
        drift = (mu - 0.5 * sigma**2) * horizon_days
        diffusion = sigma * brownian_motion

        # Calculate terminal values
        returns = np.exp(drift + diffusion)
        final_values = current_value * returns

        return SimResult(
            portfolio_id=portfolio_id,
            simulations=simulations,
            mean_value=float(np.mean(final_values)),
            median_value=float(np.median(final_values)),
            worst_case_99=float(np.percentile(final_values, 1)),
            best_case_99=float(np.percentile(final_values, 99))
        )

    async def stress_test(self, portfolio_id: int, scenario: Dict[str, float]) -> StressResult:
        """
        Apply a stress scenario.
        Scenario dict example: {"market_shock": -0.20} (20% drop)
        """
        portfolio = await self._get_portfolio(portfolio_id)
        current_value = portfolio.total_value

        # Simple stress: Apply the shock to the total value.
        # In reality, we would apply specific shocks to specific assets (stocks vs bonds).

        shock = scenario.get("market_shock", 0.0)

        stressed_value = current_value * (1 + shock)
        loss = current_value - stressed_value

        return StressResult(
            portfolio_id=portfolio_id,
            scenario_name=str(scenario),
            original_value=current_value,
            stressed_value=stressed_value,
            loss_amount=loss,
            loss_percentage=shock * -100 if shock < 0 else 0
        )
