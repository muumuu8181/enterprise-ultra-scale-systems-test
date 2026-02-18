from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.credit_risk import Counterparty, RegulatoryCapital, CreditExposure, Framework
from src.schemas.credit import CapitalResult, LimitCheckResult, Trade
import numpy as np

class CreditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_expected_loss(self, counterparty_id: int) -> float:
        result = await self.db.execute(select(Counterparty).where(Counterparty.id == counterparty_id))
        counterparty = result.scalar_one_or_none()
        if not counterparty:
            raise ValueError(f"Counterparty {counterparty_id} not found")

        # EL = PD * LGD * EAD
        return counterparty.pd_estimate * counterparty.lgd_estimate * counterparty.ead

    async def compute_regulatory_capital(self, entity_id: str, framework: str) -> CapitalResult:
        result = await self.db.execute(select(RegulatoryCapital).where(
            RegulatoryCapital.entity_id == entity_id,
            RegulatoryCapital.framework == framework
        ))
        reg_cap = result.scalar_one_or_none()

        if not reg_cap:
             return CapitalResult(tier1_capital=0.0, rwa=0.0, capital_ratio=0.0, compliance_status="UNKNOWN")

        compliance = "COMPLIANT"
        # Simple rule: Basel 3 needs > 8%, Solvency 2 needs > 100% (1.0)
        if framework == Framework.BASEL3 and reg_cap.capital_ratio < 0.08:
             compliance = "BREACH"
        elif framework == Framework.SOLVENCY2 and reg_cap.capital_ratio < 1.0:
             compliance = "BREACH"

        return CapitalResult(
            tier1_capital=reg_cap.tier1_capital,
            rwa=reg_cap.rwa,
            capital_ratio=reg_cap.capital_ratio,
            compliance_status=compliance
        )

    async def check_credit_limit(self, trade: Trade) -> LimitCheckResult:
        result = await self.db.execute(select(CreditExposure).where(
            CreditExposure.counterparty_id == trade.counterparty_id
        ))
        exposures = result.scalars().all()
        current_exposure = sum(e.mtm_value for e in exposures)

        limit = 1000000.0 # Dummy hardcoded limit
        potential_exposure = trade.nominal_amount * trade.price
        new_exposure = current_exposure + potential_exposure

        approved = new_exposure <= limit

        utilization = 0.0
        if limit > 0:
            utilization = new_exposure / limit

        return LimitCheckResult(
            is_approved=approved,
            current_exposure=current_exposure,
            limit=limit,
            utilization=utilization
        )

    def calculate_historical_var(self, data: list[float], confidence_level: float) -> float:
        """
        Calculates Value at Risk using Historical Simulation.
        data: list of historical returns/losses
        confidence_level: e.g., 0.95 or 0.99
        """
        if not data:
            return 0.0
        # If data represents returns, we look at the lower tail (negative returns)
        # If data represents losses (positive values), we look at the upper tail
        # Assuming data represents returns:
        sorted_returns = sorted(data)
        index = int((1 - confidence_level) * len(sorted_returns))
        # VaR is typically expressed as a positive number representing loss
        return abs(sorted_returns[index])

    def calculate_monte_carlo_var(self, data: list[float], simulations: int, confidence_level: float) -> float:
        """
        Calculates Value at Risk using Monte Carlo Simulation.
        """
        if not data:
            return 0.0
        mean = np.mean(data)
        std_dev = np.std(data)

        # Simulate returns
        simulated_returns = np.random.normal(mean, std_dev, simulations)

        # Use historical method on simulated data
        return self.calculate_historical_var(list(simulated_returns), confidence_level)
