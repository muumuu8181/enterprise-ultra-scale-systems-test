from sqlalchemy import Column, Integer, String, Float, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import enum
from datetime import datetime, timezone
from src.database import Base

class PlantType(str, enum.Enum):
    municipal = "municipal"
    industrial = "industrial"
    desalination = "desalination"

class PlantStatus(str, enum.Enum):
    operational = "operational"
    maintenance = "maintenance"
    offline = "offline"

class SamplePoint(str, enum.Enum):
    intake = "intake"
    pre_treatment = "pre_treatment"
    post_treatment = "post_treatment"
    distribution = "distribution"

class ChemicalType(str, enum.Enum):
    chlorine = "chlorine"
    alum = "alum"
    lime = "lime"
    polymer = "polymer"

class TreatmentPlant(Base):
    __tablename__ = "treatment_plants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Storing as Geometry. Pydantic will handle GeoJSON conversion.
    location = Column(Geometry("POINT", srid=4326), nullable=True)
    capacity_mld = Column(Float, nullable=False)
    plant_type = Column(Enum(PlantType), nullable=False)
    status = Column(Enum(PlantStatus), nullable=False)
    serving_population = Column(Integer, nullable=True)

    samples = relationship("WaterQualitySample", back_populates="plant")
    dosings = relationship("ChemicalDosing", back_populates="plant")

class WaterQualitySample(Base):
    __tablename__ = "water_quality_samples"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("treatment_plants.id"), nullable=False)
    sample_point = Column(Enum(SamplePoint), nullable=False)
    ph = Column(Float, nullable=True)
    turbidity_ntu = Column(Float, nullable=True)
    chlorine_ppm = Column(Float, nullable=True)
    tds_ppm = Column(Float, nullable=True)
    e_coli_count = Column(Integer, nullable=True)
    sampled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    compliant = Column(Boolean, default=True)

    plant = relationship("TreatmentPlant", back_populates="samples")

class ChemicalDosing(Base):
    __tablename__ = "chemical_dosings"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("treatment_plants.id"), nullable=False)
    chemical = Column(Enum(ChemicalType), nullable=False)
    dosage_mg_l = Column(Float, nullable=True)
    flow_rate = Column(Float, nullable=True)
    tank_level_pct = Column(Float, nullable=True)
    auto_adjusted = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    plant = relationship("TreatmentPlant", back_populates="dosings")
