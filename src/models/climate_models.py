from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SqEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from src.db.base import Base

class ModelType(str, enum.Enum):
    REGIONAL = "regional"
    GLOBAL = "global"

class WeatherStation(Base):
    __tablename__ = "weather_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float)
    status = Column(String, default="active")
    last_reading_at = Column(DateTime, nullable=True)

    readings = relationship("ClimateReading", back_populates="station")

class ClimateReading(Base):
    __tablename__ = "climate_readings"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, ForeignKey("weather_stations.station_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_dir = Column(Float)
    precipitation = Column(Float)

    station = relationship("WeatherStation", back_populates="readings")

class ClimateModel(Base):
    __tablename__ = "climate_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model_type = Column(SqEnum(ModelType), nullable=False)
    resolution_km = Column(Float)
    forecast_hours = Column(Integer)
    accuracy_score = Column(Float)
