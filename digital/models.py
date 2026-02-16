from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from distribution.models import Movie, Theater

@dataclass
class DCP:
    """Represents a Digital Cinema Package."""
    movie: Movie
    version: str
    format: str = "JPEG 2000"
    encrypted: bool = True
    size_gb: float = 0.0

@dataclass
class KDM:
    """Represents a Key Delivery Message."""
    dcp: DCP
    theater: Theater
    valid_from: datetime
    valid_until: datetime
    uuid: str  # Unique identifier for the KDM

    def is_valid(self, check_time: Optional[datetime] = None) -> bool:
        """Checks if the KDM is valid at the given time."""
        if check_time is None:
            check_time = datetime.now()
        return self.valid_from <= check_time <= self.valid_until
