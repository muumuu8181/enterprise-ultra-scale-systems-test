from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class BuildingTwin(Base):
    __tablename__ = 'building_twins'

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(String, unique=True, index=True)
    floors = Column(Integer)
    total_area_sqm = Column(Float)
    occupancy_current = Column(Integer)
    hvac_zones = Column(JSON)
    energy_kwh_today = Column(Float)

    floor_plans = relationship("FloorPlan", back_populates="building_twin")
    energy_readings = relationship("EnergyReading", back_populates="building")

class FloorPlan(Base):
    __tablename__ = 'floor_plans'

    id = Column(Integer, primary_key=True, index=True)
    building_twin_id = Column(Integer, ForeignKey('building_twins.id'))
    floor_number = Column(Integer)
    layout_svg = Column(String)
    rooms = Column(JSON)
    sensors = Column(JSON)

    building_twin = relationship("BuildingTwin", back_populates="floor_plans")

class EnergyReading(Base):
    __tablename__ = 'energy_readings'

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey('building_twins.id'))
    zone_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    kwh_consumed = Column(Float)
    temperature_setpoint = Column(Float)
    actual_temp = Column(Float)

    building = relationship("BuildingTwin", back_populates="energy_readings")
