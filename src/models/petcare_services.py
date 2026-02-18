from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import datetime
import enum

Base = declarative_base()

class ServiceType(str, enum.Enum):
    grooming = "grooming"
    boarding = "boarding"
    daycare = "daycare"
    training = "training"
    vet = "vet"

class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"

class ServiceProvider(Base):
    __tablename__ = 'service_providers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    service_types = Column(JSON, nullable=False)  # List of ServiceType as strings
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    rating = Column(Float, default=0.0)
    verified = Column(Boolean, default=False)
    availability = Column(JSON)  # Schedule structure

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, nullable=False)
    provider_id = Column(Integer, ForeignKey('service_providers.id'), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    price = Column(Float, nullable=False)

    provider = relationship("ServiceProvider")

class DailyReport(Base):
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    activities = Column(JSON)
    meals_given = Column(Integer, default=0)
    behavior_notes = Column(String)
    photos = Column(JSON)  # List of photo URLs

    booking = relationship("Booking")
