from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import enum
from datetime import datetime

Base = declarative_base()

class TurbineStatus(enum.Enum):
    OPERATING = "operating"
    IDLE = "idle"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

class TaskType(enum.Enum):
    SCHEDULED = "scheduled"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"

class ComponentType(enum.Enum):
    GEARBOX = "gearbox"
    GENERATOR = "generator"
    BLADE = "blade"
    BEARING = "bearing"
    YAW = "yaw"

class WindFarm(Base):
    __tablename__ = 'wind_farms'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # location: GeoJSON. Using Geometry('POINT') for simplicity as location implies a point usually.
    # If it was a polygon, we'd use POLYGON. Given "location", POINT is standard for a farm reference point.
    location = Column(Geometry('POINT', srid=4326))
    capacity_mw = Column(Float)
    turbine_count = Column(Integer)
    turbine_model = Column(String)
    hub_height_m = Column(Float)
    rotor_diameter_m = Column(Float)
    commissioned_date = Column(DateTime)

    turbines = relationship("Turbine", back_populates="farm")

class Turbine(Base):
    __tablename__ = 'turbines'

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('wind_farms.id'))
    turbine_number = Column(String)
    status = Column(Enum(TurbineStatus), default=TurbineStatus.IDLE)
    power_output_kw = Column(Float)
    wind_speed_ms = Column(Float)
    rotor_rpm = Column(Float)
    yaw_angle = Column(Float)
    pitch_angle = Column(Float)
    nacelle_temp_c = Column(Float)

    farm = relationship("WindFarm", back_populates="turbines")
    maintenance_tasks = relationship("MaintenanceTask", back_populates="turbine")

class MaintenanceTask(Base):
    __tablename__ = 'maintenance_tasks'

    id = Column(Integer, primary_key=True, index=True)
    turbine_id = Column(Integer, ForeignKey('turbines.id'))
    task_type = Column(Enum(TaskType))
    component = Column(Enum(ComponentType))
    priority = Column(Integer)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    technician_id = Column(String)
    downtime_hours = Column(Float)

    turbine = relationship("Turbine", back_populates="maintenance_tasks")
