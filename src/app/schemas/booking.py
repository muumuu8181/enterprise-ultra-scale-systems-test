from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from enum import Enum

class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

class BookingBase(BaseModel):
    passenger_name: str
    passenger_email: EmailStr
    flight_id: int
    seat_id: Optional[int] = None
    status: BookingStatus = BookingStatus.PENDING

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    pnr: str

    model_config = ConfigDict(from_attributes=True)
