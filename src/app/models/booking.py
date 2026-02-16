from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from src.app.database import Base

class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    pnr = Column(String, unique=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=True)
    passenger_name = Column(String)
    passenger_email = Column(String)
    status = Column(String, default=BookingStatus.PENDING)

    flight = relationship("Flight", back_populates="bookings")
    seat = relationship("Seat")
