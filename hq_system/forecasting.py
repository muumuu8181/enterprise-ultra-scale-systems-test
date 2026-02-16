from typing import List, Dict
from shared.models import Transaction

def predict_order(product_id: str, sales_history: List[Transaction]) -> int:
    """
    Simple moving average forecasting.
    In a real system, this would use time-series analysis (ARIMA, Prophet, etc).
    """
    total_sold = 0
    count = 0

    # Calculate total sold for this product across all transactions
    for txn in sales_history:
        for item in txn.items:
            if item.product_id == product_id:
                total_sold += item.quantity
                count += 1

    if count == 0:
        return 10  # Default stock level

    # Very basic logic: Replenish to average * 2
    avg_per_txn = total_sold / max(1, count)
    return int(avg_per_txn * 5) # Stock for 5 sales
