from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from sqlalchemy.orm import mapped_column
from geoalchemy2 import Geometry
from src.database import Base
import enum

class DisruptionType(str, enum.Enum):
    SIGNAL = "signal"
    WEATHER = "weather"
    ACCIDENT = "accident"
    MAINTENANCE = "maintenance"

class MaintenanceWindowType(str, enum.Enum):
    PLANNED = "planned"
    EMERGENCY = "emergency"

class Station(Base):
    __tablename__ = "stations"
    id = mapped_column(Integer, primary_key=True, index=True)
    name = mapped_column(String, nullable=False)
    city = mapped_column(String)
    location = mapped_column(Geometry("POINT"))
    platforms = mapped_column(Integer)
    facilities = mapped_column(JSON)
    accessibility = mapped_column(JSON)

class NetworkDisruption(Base):
    __tablename__ = "network_disruptions"
    id = mapped_column(Integer, primary_key=True, index=True)
    disruption_type = mapped_column(Enum(DisruptionType))
    affected_lines = mapped_column(JSON)
    start_time = mapped_column(DateTime)
    estimated_end = mapped_column(DateTime)
    passenger_impact = mapped_column(String)

class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"
    id = mapped_column(Integer, primary_key=True, index=True)
    line_id = mapped_column(String)
    window_type = mapped_column(Enum(MaintenanceWindowType))
    start_time = mapped_column(DateTime)
    end_time = mapped_column(DateTime)
    replacement_service = mapped_column(JSON)
