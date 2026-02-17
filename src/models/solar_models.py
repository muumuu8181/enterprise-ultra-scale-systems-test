from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime

Base = declarative_base()

class PanelType(enum.Enum):
    MONO = "mono"
    POLY = "poly"
    THIN_FILM = "thin_film"

class ArrayStatus(enum.Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OFFLINE = "offline"

class SolarFarm(Base):
    __tablename__ = 'solar_farms'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(JSON)  # GeoJSON
    capacity_mw = Column(Float)
    panel_count = Column(Integer)
    panel_type = Column(Enum(PanelType))
    inverter_count = Column(Integer)
    commissioned_date = Column(DateTime)
    grid_connection_point = Column(String)

    arrays = relationship("PanelArray", back_populates="farm")
    energy_outputs = relationship("EnergyOutput", back_populates="farm")

class PanelArray(Base):
    __tablename__ = 'panel_arrays'

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('solar_farms.id'))
    array_number = Column(String)
    panel_count = Column(Integer)
    tilt_angle = Column(Float)
    azimuth = Column(Float)
    status = Column(Enum(ArrayStatus))
    efficiency_pct = Column(Float)
    last_cleaned = Column(DateTime)

    farm = relationship("SolarFarm", back_populates="arrays")
    energy_outputs = relationship("EnergyOutput", back_populates="array")

class EnergyOutput(Base):
    __tablename__ = 'energy_outputs'

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('solar_farms.id'))
    array_id = Column(Integer, ForeignKey('panel_arrays.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    power_kw = Column(Float)
    irradiance_w_m2 = Column(Float)
    ambient_temp_c = Column(Float)
    panel_temp_c = Column(Float)
    performance_ratio = Column(Float)
    curtailment_kw = Column(Float)

    farm = relationship("SolarFarm", back_populates="energy_outputs")
    array = relationship("PanelArray", back_populates="energy_outputs")
