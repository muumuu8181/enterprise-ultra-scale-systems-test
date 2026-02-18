from typing import List
from pydantic import BaseModel
from datetime import datetime
from src.models.finance_models import Transaction

class Alert(BaseModel):
    id: str
    message: str
    severity: str
    timestamp: datetime

class NetWorthReport(BaseModel):
    user_id: int
    total_assets: float
    total_liabilities: float
    net_worth: float
    currency: str = "USD"
    generated_at: datetime

async def auto_categorize(transaction: Transaction) -> str:
    """
    Automatically categorizes a transaction based on its merchant or other details.
    """
    if not transaction.merchant:
        return "Uncategorized"

    merchant = transaction.merchant.lower()
    if "coffee" in merchant or "starbucks" in merchant:
        return "Food & Drink"
    elif "uber" in merchant or "lyft" in merchant:
        return "Transportation"
    elif "amazon" in merchant:
        return "Shopping"
    elif "salary" in merchant or "payroll" in merchant:
        return "Income"

    return "General"

async def detect_unusual_spending(user_id: int) -> List[Alert]:
    """
    Detects unusual spending patterns for a user.
    """
    # Placeholder logic
    # In a real implementation, this would query the database for recent transactions
    # and compare them against historical averages or thresholds.

    return [
        Alert(
            id="alert-123",
            message="Unusual high spending detected in category 'Shopping'",
            severity="medium",
            timestamp=datetime.now()
        )
    ]

async def calculate_net_worth(user_id: int) -> NetWorthReport:
    """
    Calculates the net worth of a user by aggregating account balances.
    """
    # Placeholder logic
    # In a real implementation, this would query the database for all accounts belonging to the user.

    return NetWorthReport(
        user_id=user_id,
        total_assets=15000.00,
        total_liabilities=500.00,
        net_worth=14500.00,
        generated_at=datetime.now()
    )
