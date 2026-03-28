from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

class VoyageStatus(enum.Enum):
    booking = "booking"
    boarding = "boarding"
    sailing = "sailing"
    docked = "docked"
    completed = "completed"

class CabinType(enum.Enum):
    inside = "inside"
    ocean_view = "ocean_view"
    balcony = "balcony"
    suite = "suite"

class CabinStatus(enum.Enum):
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"

class Voyage(Base):
    __tablename__ = 'voyages'
    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, nullable=False)
    itinerary = Column(JSON)
    departure_port = Column(String)
    departure_date = Column(DateTime)
    return_date = Column(DateTime)
    capacity_passengers = Column(Integer)
    booked_count = Column(Integer, default=0)
    status = Column(Enum(VoyageStatus), default=VoyageStatus.booking)

    port_calls = relationship("PortCall", back_populates="voyage")

class Cabin(Base):
    __tablename__ = 'cabins'
    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, nullable=False)
    deck = Column(String)
    cabin_number = Column(String)
    cabin_type = Column(Enum(CabinType))
    capacity = Column(Integer)
    price_per_night = Column(Float)
    status = Column(Enum(CabinStatus), default=CabinStatus.available)
    amenities = Column(JSON)

class PortCall(Base):
    __tablename__ = 'port_calls'
    id = Column(Integer, primary_key=True, index=True)
    voyage_id = Column(Integer, ForeignKey('voyages.id'))
    port_name = Column(String)
    country = Column(String)
    arrival_time = Column(DateTime)
    departure_time = Column(DateTime)
    excursions_available = Column(JSON)
    tender_required = Column(Boolean, default=False)
    customs_clearance = Column(Boolean, default=False)

    voyage = relationship("Voyage", back_populates="port_calls")
