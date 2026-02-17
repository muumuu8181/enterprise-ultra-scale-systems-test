import asyncio

async def calculate_mrr() -> float:
    # Dummy implementation as requested
    # In a real scenario, this would aggregate active subscriptions
    await asyncio.sleep(0.1) # Simulate DB latency
    return 100000.0

async def compute_ltv(customer_id: str) -> float:
    # Dummy implementation
    await asyncio.sleep(0.1)
    return 5000.0

async def forecast_churn(cohort: str) -> float:
    # Dummy implementation
    # Returns a percentage
    await asyncio.sleep(0.1)
    return 0.05

def calculate_proration(amount: float, total_days: int, days_used: int) -> float:
    """
    Calculates the prorated amount based on usage.
    """
    if total_days == 0:
        return 0.0
    daily_rate = amount / total_days
    return daily_rate * days_used
