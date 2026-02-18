from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.ground_ops import CrewType, TurnaroundStatus, CarouselStatus

class GroundCrewSchema(BaseModel):
    id: int
    crew_type: CrewType
    shift: str
    assigned_flight_id: Optional[str]
    check_in_time: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class TurnaroundSchema(BaseModel):
    id: int
    flight_id: str
    target_minutes: int
    actual_minutes: Optional[int] = None
    steps_completed: Optional[List[Dict[str, Any]]] = []
    status: TurnaroundStatus

    model_config = ConfigDict(from_attributes=True)

class BaggageCarouselSchema(BaseModel):
    id: int
    terminal: str
    carousel_number: int
    status: CarouselStatus
    assigned_flight_id: Optional[str] = None
    bags_claimed: int = 0

    model_config = ConfigDict(from_attributes=True)
