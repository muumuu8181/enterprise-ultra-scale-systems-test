from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey
from geoalchemy2 import Geometry
from src.database import Base
import enum
from datetime import datetime

class IrrigationType(str, enum.Enum):
    drip = "drip"
    sprinkler = "sprinkler"
    flood = "flood"
    rainfed = "rainfed"

class SensorType(str, enum.Enum):
    soil_moisture = "soil_moisture"
    temperature = "temperature"
    humidity = "humidity"
    ndvi = "ndvi"
    rain_gauge = "rain_gauge"

class SensorStatus(str, enum.Enum):
    active = "active"
    low_battery = "low_battery"
    offline = "offline"

class PrescriptionType(str, enum.Enum):
    fertilizer = "fertilizer"
    pesticide = "pesticide"
    irrigation = "irrigation"
    harvest = "harvest"

class PrescriptionStatus(str, enum.Enum):
    planned = "planned"
    applied = "applied"
    skipped = "skipped"

class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String, index=True)
    name = Column(String)
    location = Column(Geometry("POLYGON", srid=4326))
    area_hectares = Column(Float)
    crop_type = Column(String)
    soil_type = Column(String)
    irrigation_type = Column(Enum(IrrigationType))
    planting_date = Column(Date)
    expected_harvest = Column(Date)

class SensorNode(Base):
    __tablename__ = "sensor_nodes"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"))
    sensor_type = Column(Enum(SensorType))
    location = Column(Geometry("POINT", srid=4326))
    battery_pct = Column(Float)
    last_reading_at = Column(DateTime)
    status = Column(Enum(SensorStatus))

class CropPrescription(Base):
    __tablename__ = "crop_prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"))
    prescription_type = Column(Enum(PrescriptionType))
    product = Column(String)
    quantity = Column(Float)
    application_method = Column(String)
    scheduled_date = Column(Date)
    applied_date = Column(Date, nullable=True)
    status = Column(Enum(PrescriptionStatus))
