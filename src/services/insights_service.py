from datetime import datetime, timezone
from src.models.financial_insights import SpendingAnalysis, FinancialScore

async def compute_spending_analysis(user_id: str, period: str) -> SpendingAnalysis:
    # Mock implementation
    return SpendingAnalysis(
        id="analysis_123",
        user_id=user_id,
        period=period,
        category_breakdown={"Food": 500.0, "Transport": 200.0, "Utilities": 150.0},
        total_spend=850.0,
        vs_previous_period_pct=5.2
    )

async def calculate_financial_health_score(user_id: str) -> FinancialScore:
    # Mock implementation
    return FinancialScore(
        id="score_456",
        user_id=user_id,
        calculated_at=datetime.now(timezone.utc),
        credit_utilization=0.3,
        savings_rate=0.2,
        expense_ratio=0.5,
        score_0_850=750
    )

async def generate_tax_summary(user_id: str, tax_year: int) -> dict:
    # Mock implementation
    return {
        "user_id": user_id,
        "tax_year": tax_year,
        "total_income": 60000.0,
        "deductible_expenses": 12000.0,
        "taxable_income": 48000.0,
        "estimated_tax": 9600.0
    }
