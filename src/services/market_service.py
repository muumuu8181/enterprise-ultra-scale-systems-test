from typing import List, Any
import random
from src.models.energy_models import EnergyTrade

async def clear_market(period: str) -> List[EnergyTrade]:
    """
    Clears the market for the given period.
    Returns a list of matched trades.
    """
    # Mock implementation
    # Returns an empty list as we don't have a persistent store of bids to match against
    return []

async def calculate_clearing_price(bids: list, asks: list) -> float:
    """
    Calculates the market clearing price based on bids and asks.
    Assumes bids and asks are lists of dictionaries or objects with a 'price' attribute.
    """
    if not bids or not asks:
        return 0.0

    # robustly handle dict or object access
    def get_price(item):
        if isinstance(item, dict):
            return item.get('price', 0.0)
        return getattr(item, 'price', 0.0)

    avg_bid = sum(get_price(b) for b in bids) / len(bids)
    avg_ask = sum(get_price(a) for a in asks) / len(asks)

    return (avg_bid + avg_ask) / 2

async def forecast_demand(region: str, hours: int) -> List[float]:
    """
    Forecasts demand for the given region for the next 'hours'.
    """
    base_demand = 100.0
    return [base_demand + random.uniform(-10, 10) for _ in range(hours)]
