from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="available")  # available, rented, maintenance
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    current_speed = Column(Float, default=0.0)
    fuel_level = Column(Float, default=100.0)
    mileage = Column(Float, default=0.0)

    bookings = relationship("Booking", back_populates="vehicle")
    telematics_logs = relationship("TelematicsData", back_populates="vehicle")
    alerts = relationship("VehicleAlert", back_populates="vehicle")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    user_id = Column(Integer) # Placeholder
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="active") # active, completed, cancelled
    total_price = Column(Float, default=0.0)

    vehicle = relationship("Vehicle", back_populates="bookings")
    claims = relationship("DamageClaim", back_populates="booking")

class TelematicsData(Base):
    __tablename__ = "telematics_data"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    fuel_level = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="telematics_logs")

class VehicleAlert(Base):
    __tablename__ = "vehicle_alerts"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    alert_type = Column(String) # breakdown, accident, geofence_violation
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

    vehicle = relationship("Vehicle", back_populates="alerts")

class DamageClaim(Base):
    __tablename__ = "damage_claims"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    description = Column(Text)
    photos = Column(JSON) # List of photo URLs or base64
    status = Column(String, default="pending") # pending, under_assessment, resolved, rejected
    assessment_notes = Column(Text, nullable=True)
    resolved_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = relationship("Booking", back_populates="claims")
