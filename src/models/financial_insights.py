from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class SpendingAnalysis(BaseModel):
    id: str
    user_id: str
    period: str
    category_breakdown: Dict[str, float]
    total_spend: float
    vs_previous_period_pct: float

class BudgetRule(BaseModel):
    id: str
    user_id: str
    category: str
    monthly_limit: float
    alert_at_pct: float
    current_spend: float

class FinancialScore(BaseModel):
    id: str
    user_id: str
    calculated_at: datetime
    credit_utilization: float
    savings_rate: float
    expense_ratio: float
    score_0_850: int
