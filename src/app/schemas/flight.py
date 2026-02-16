from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class SeatBase(BaseModel):
    seat_number: str
    class_type: str
    is_booked: bool = False

class SeatCreate(SeatBase):
    pass

class Seat(SeatBase):
    id: int
    flight_id: int

    model_config = ConfigDict(from_attributes=True)

class FlightBase(BaseModel):
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    capacity: int

class FlightCreate(FlightBase):
    seats: List[SeatCreate] = []

class Flight(FlightBase):
    id: int
    seats: List[Seat] = []

    model_config = ConfigDict(from_attributes=True)
