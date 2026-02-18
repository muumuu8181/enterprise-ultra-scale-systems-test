import pytest
from src.services.insights_service import compute_spending_analysis, calculate_financial_health_score
from src.models.financial_insights import SpendingAnalysis, FinancialScore

@pytest.mark.asyncio
async def test_compute_spending_analysis_structure():
    user_id = "test_user"
    period = "month"

    result = await compute_spending_analysis(user_id, period)

    assert isinstance(result, SpendingAnalysis)
    assert result.user_id == user_id
    assert result.period == period
    assert isinstance(result.category_breakdown, dict)
    assert "Food" in result.category_breakdown
    assert result.total_spend > 0

@pytest.mark.asyncio
async def test_calculate_financial_health_score_range():
    user_id = "test_user"

    result = await calculate_financial_health_score(user_id)

    assert isinstance(result, FinancialScore)
    assert result.user_id == user_id
    assert 0 <= result.score_0_850 <= 850
    assert 0 <= result.credit_utilization <= 1.0
    assert 0 <= result.savings_rate <= 1.0
