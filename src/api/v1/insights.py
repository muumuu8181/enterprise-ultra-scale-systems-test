from fastapi import APIRouter, Query, Body, HTTPException
from typing import Dict, Any, List
from src.services.insights_service import compute_spending_analysis, calculate_financial_health_score, generate_tax_summary
from src.models.financial_insights import BudgetRule, SpendingAnalysis, FinancialScore

router = APIRouter()

@router.get("/insights/spending-breakdown", response_model=SpendingAnalysis)
async def get_spending_breakdown(period: str = Query("month"), user_id: str = "user_1"):
    return await compute_spending_analysis(user_id, period)

@router.get("/insights/trends")
async def get_trends(user_id: str = "user_1"):
    # Dummy implementation for trends
    return {
        "user_id": user_id,
        "trends": [
            {"month": "2023-01", "spend": 1000},
            {"month": "2023-02", "spend": 1100},
            {"month": "2023-03", "spend": 950}
        ]
    }

@router.post("/budgets/set")
async def set_budget(budget: BudgetRule):
    # Dummy implementation
    return {"status": "success", "budget_id": budget.id}

@router.get("/budgets/status")
async def get_budget_status(user_id: str = "user_1"):
    # Dummy implementation
    return {
        "user_id": user_id,
        "budgets": [
            {"category": "Food", "limit": 500, "current": 350, "status": "ok"},
            {"category": "Transport", "limit": 200, "current": 210, "status": "exceeded"}
        ]
    }

@router.get("/financial-score", response_model=FinancialScore)
async def get_financial_score(user_id: str = "user_1"):
    return await calculate_financial_health_score(user_id)

@router.post("/insights/export-for-tax")
async def export_for_tax(user_id: str = Body(..., embed=True), tax_year: int = Body(..., embed=True)):
    return await generate_tax_summary(user_id, tax_year)
