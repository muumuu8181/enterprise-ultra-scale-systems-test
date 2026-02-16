from dataclasses import dataclass
from datetime import date
from typing import List
from distribution.models import Movie, Theater, ScreeningContract

@dataclass
class DailyRevenue:
    """Represents the daily box office revenue for a movie in a theater."""
    date: date
    theater: Theater
    movie: Movie
    gross_revenue: float
    attendance: int

    def calculate_distributor_share(self, contract: ScreeningContract) -> float:
        """Calculates the distributor's share of the revenue based on the percentage."""
        if contract.movie != self.movie or contract.theater != self.theater:
            raise ValueError("Contract does not match the movie or theater.")

        return self.gross_revenue * (contract.revenue_share_percentage / 100.0)

@dataclass
class Settlement:
    """Represents the settlement calculation for a screening contract."""
    contract: ScreeningContract
    daily_revenues: List[DailyRevenue]

    def calculate_total_distributor_share(self) -> float:
        """Calculates the total distributor share, considering the Minimum Guarantee."""
        total_share = 0.0
        for revenue in self.daily_revenues:
            # Using the daily percentage calculation
            total_share += revenue.calculate_distributor_share(self.contract)

        return max(total_share, self.contract.minimum_guarantee)
