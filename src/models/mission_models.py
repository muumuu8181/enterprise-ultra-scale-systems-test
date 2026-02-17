from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from src.models.base import Base
import datetime

class Satellite(Base):
    __tablename__ = "satellites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tle_line1 = Column(String)
    tle_line2 = Column(String)
    status = Column(String, default="operational")
    health_metrics = Column(JSON, default={})
    orbit_params = Column(JSON, default={})

    telemetry = relationship("Telemetry", back_populates="satellite")
    anomalies = relationship("AnomalyLog", back_populates="satellite")
    alert_config = relationship("AlertConfiguration", back_populates="satellite", uselist=False)

class GroundStation(Base):
    __tablename__ = "ground_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float) # meters
    min_elevation_angle = Column(Float, default=10.0) # degrees

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(JSON)

    satellite = relationship("Satellite", back_populates="telemetry")

class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id = Column(Integer, primary_key=True, index=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"))
    severity = Column(String)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    recommended_action = Column(String)

    satellite = relationship("Satellite", back_populates="anomalies")

class AlertConfiguration(Base):
    __tablename__ = "alert_configurations"

    id = Column(Integer, primary_key=True, index=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"))
    thresholds = Column(JSON)

    satellite = relationship("Satellite", back_populates="alert_config")
