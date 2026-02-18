from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSON
from geoalchemy2 import Geography
import datetime

Base = declarative_base()

class Sensor(Base):
    __tablename__ = 'sensors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    status = Column(String, default='active')
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class SensorReading(Base):
    __tablename__ = 'sensor_readings'

    time = Column(DateTime, nullable=False, primary_key=True)
    # Logical foreign key to sensors.id, but lives in a separate TimescaleDB instance
    sensor_id = Column(Integer, nullable=False, primary_key=True)
    value = Column(Float, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True) # metadata is reserved in Base

class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_resolved = Column(Boolean, default=False)

class TrafficSignal(Base):
    __tablename__ = 'traffic_signals'

    id = Column(Integer, primary_key=True)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    status = Column(String, default='red')
    intersection_id = Column(String, nullable=True)

class EmergencyIncident(Base):
    __tablename__ = 'emergency_incidents'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    status = Column(String, default='reported')
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
