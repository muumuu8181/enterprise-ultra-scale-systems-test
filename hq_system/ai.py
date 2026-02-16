from typing import List

def predict_demand(sales_history: List[int]) -> int:
    """
    Simple Moving Average forecast.
    """
    if not sales_history:
        return 0
    return int(sum(sales_history) / len(sales_history))
