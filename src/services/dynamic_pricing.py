class DynamicPricingService:
    def calculate_surge(self, demand: float, supply: float) -> float:
        """
        Calculates surge multiplier based on demand and supply.
        """
        if supply <= 0:
            return 2.0  # Max surge if no supply

        ratio = demand / supply
        if ratio >= 1.5:
            return 1.5
        elif ratio >= 1.2:
            return 1.2
        elif ratio > 1.0:
            return 1.1
        else:
            return 1.0

    def seasonal_adjustment(self, season: str) -> float:
        """
        Returns a price multiplier based on the season.
        """
        seasons = {
            "high": 1.5,
            "peak": 2.0,
            "low": 0.8,
            "standard": 1.0
        }
        return seasons.get(season.lower(), 1.0)

    def discount_long_term(self, days: int) -> float:
        """
        Returns a discount percentage (as a decimal, e.g., 0.10 for 10%) if rental is 7 days or more.
        """
        if days >= 7:
            return 0.10
        return 0.0

    def calculate_excess_mileage(self, mileage: float, limit: float, rate_per_mile: float = 0.50) -> float:
        """
        Calculates the cost for excess mileage.
        """
        if mileage > limit:
            excess = mileage - limit
            return excess * rate_per_mile
        return 0.0
