from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class EquipmentCriticality(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"

class SensorType(str, enum.Enum):
    vibration = "vibration"
    temperature = "temperature"
    current = "current"
    pressure = "pressure"

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    install_date = Column(DateTime, default=datetime.utcnow)
    location = Column(String, nullable=False)
    criticality = Column(SAEnum(EquipmentCriticality), nullable=False)

    sensor_data = relationship("SensorData", back_populates="equipment")
    predictions = relationship("FailurePrediction", back_populates="equipment")

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    sensor_type = Column(SAEnum(SensorType), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    equipment = relationship("Equipment", back_populates="sensor_data")

class FailurePrediction(Base):
    __tablename__ = "failure_predictions"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    predicted_failure_date = Column(DateTime, nullable=False)
    failure_mode = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    remaining_useful_life_days = Column(Float, nullable=False)

    equipment = relationship("Equipment", back_populates="predictions")
