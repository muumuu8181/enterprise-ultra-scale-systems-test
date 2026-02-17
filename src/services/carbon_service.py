from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.carbon_models import EmissionSource, CarbonCredit, CreditStatus
from typing import List, Dict, Any

class CarbonService:
    async def calculate_carbon_footprint(self, db: AsyncSession, entity_id: str, year: int) -> float:
        """
        Calculates the total carbon footprint for an entity for a given year.
        Note: The current model does not strictly support 'year' filtering for EmissionSource,
        so we sum all sources for the entity as a mock implementation.
        """
        stmt = select(EmissionSource).where(EmissionSource.entity_id == entity_id)
        result = await db.execute(stmt)
        sources = result.scalars().all()
        return sum(s.reported_co2_kt for s in sources)

    async def optimize_offset_portfolio(self, db: AsyncSession, budget: float) -> List[CarbonCredit]:
        """
        Selects a portfolio of carbon credits that fits within the budget.
        Assumption: Price is $10 per ton of CO2.
        """
        price_per_ton = 10.0
        max_volume = budget / price_per_ton

        stmt = select(CarbonCredit).where(CarbonCredit.status == CreditStatus.ISSUED).order_by(CarbonCredit.volume_tco2.desc())
        result = await db.execute(stmt)
        credits = result.scalars().all()

        selected = []
        current_volume = 0
        for credit in credits:
            if current_volume + credit.volume_tco2 <= max_volume:
                selected.append(credit)
                current_volume += credit.volume_tco2
        return selected

    async def generate_netzero_pathway(self, db: AsyncSession, entity_id: str) -> Dict[str, Any]:
        """
        Generates an AI-driven roadmap for achieving net zero.
        """
        # Mock AI logic
        return {
            "entity_id": entity_id,
            "steps": [
                {"year": 2025, "action": "Switch to renewable energy", "reduction_tco2": 500},
                {"year": 2030, "action": "Electrify fleet", "reduction_tco2": 1200},
                {"year": 2040, "action": "Carbon capture implementation", "reduction_tco2": 3000}
            ],
            "target_year": 2050,
            "status": "AI Roadmap Generated"
        }
