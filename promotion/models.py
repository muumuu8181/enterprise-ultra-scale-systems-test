from dataclasses import dataclass
from enum import Enum
from datetime import date

class PromotionType(Enum):
    TRAILER = "Trailer"
    POSTER = "Poster"
    FLYER = "Flyer"
    TV_CM = "TV CM"
    NEWSPAPER_AD = "Newspaper Ad"
    WEB_AD = "Web Ad"
    PRESS_PREVIEW = "Press Preview"
    GENERAL_PREVIEW = "General Preview"

@dataclass
class PromotionMaterial:
    """Represents a promotion material."""
    title: str
    type: PromotionType
    url: str  # URL or file path

@dataclass
class PromotionCost:
    """Represents a promotion cost."""
    title: str
    type: PromotionType
    cost: float
    date: date
