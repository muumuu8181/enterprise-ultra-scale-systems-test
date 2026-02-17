from typing import List
from src.schemas.planning_schemas import SavingsPlan, TradeRecommendation, ActionType

async def generate_savings_plan(goal_id: int) -> SavingsPlan:
    # Mock implementation
    return SavingsPlan(
        goal_id=goal_id,
        monthly_contribution_suggested=500.0,
        projected_completion_date="2025-12-31",
        risk_level="conservative"
    )

async def suggest_rebalancing(user_id: int) -> List[TradeRecommendation]:
    # Mock implementation
    return [
        TradeRecommendation(
            symbol="SPY",
            asset_type="etf",
            action=ActionType.buy,
            quantity=10.0,
            current_allocation=0.4,
            target_allocation=0.5,
            reason="Underweight in US Equities"
        )
    ]
