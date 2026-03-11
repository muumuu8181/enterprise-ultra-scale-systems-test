from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class ActionType(str, Enum):
    buy = "buy"
    sell = "sell"

class SavingsPlan(BaseModel):
    goal_id: int
    monthly_contribution_suggested: float
    projected_completion_date: str
    risk_level: str

class TradeRecommendation(BaseModel):
    symbol: str
    asset_type: str
    action: ActionType
    quantity: float
    current_allocation: float
    target_allocation: float
    reason: str
