from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.app.database import Base

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String, unique=True, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    departure_time = Column(DateTime)
    capacity = Column(Integer)

    seats = relationship("Seat", back_populates="flight")
    bookings = relationship("Booking", back_populates="flight")

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_number = Column(String)
    class_type = Column(String)
    is_booked = Column(Boolean, default=False)

    flight = relationship("Flight", back_populates="seats")
