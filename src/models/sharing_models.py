from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import enum
from datetime import datetime

Base = declarative_base()

class VehicleType(str, enum.Enum):
    BIKE = "bike"
    E_BIKE = "e_bike"
    SCOOTER = "scooter"

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"

class StationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Vehicle(Base):
    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_type = Column(SAEnum(VehicleType), nullable=False)
    serial_number = Column(String, unique=True, nullable=False)
    battery_level_pct = Column(Float, default=100.0)
    # Using Geometry type from GeoAlchemy2. srid 4326 is WGS 84.
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    status = Column(SAEnum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    last_maintained = Column(DateTime, default=datetime.utcnow)

class Ride(Base):
    __tablename__ = 'rides'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    start_location = Column(Geometry(geometry_type='POINT', srid=4326))
    end_location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    distance_km = Column(Float, default=0.0)
    calories_burned = Column(Float, default=0.0)
    fare = Column(Float, default=0.0)
    payment_id = Column(String, nullable=True)

    vehicle = relationship("Vehicle")

class Station(Base):
    __tablename__ = 'stations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    capacity = Column(Integer, default=0)
    available_vehicles = Column(Integer, default=0)
    available_docks = Column(Integer, default=0)
    status = Column(SAEnum(StationStatus), default=StationStatus.ACTIVE)
    zone = Column(String, nullable=True)
