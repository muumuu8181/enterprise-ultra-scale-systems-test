from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

@dataclass
class Movie:
    """Represents a movie."""
    title: str
    release_date: date
    rating: str
    distributor: str

@dataclass
class Theater:
    """Represents a movie theater."""
    name: str
    location: str
    capacity: int

@dataclass
class ScreeningContract:
    """Represents a contract between a distributor and a theater."""
    movie: Movie
    theater: Theater
    revenue_share_percentage: float  # Percentage of box office revenue for the distributor
    minimum_guarantee: float = 0.0

@dataclass
class ScreeningSchedule:
    """Represents the screening schedule for a movie in a theater."""
    movie: Movie
    theater: Theater
    start_date: date
    end_date: date
    showtimes: List[datetime]
