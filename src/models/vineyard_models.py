from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, Enum as SAEnum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import enum
from src.database import Base

class QualityGrade(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"

class WineType(str, enum.Enum):
    RED = "red"
    WHITE = "white"
    ROSE = "rose"
    SPARKLING = "sparkling"

class AgingVessel(str, enum.Enum):
    BARREL = "barrel"
    TANK = "tank"
    BOTTLE = "bottle"

class WineStatus(str, enum.Enum):
    FERMENTING = "fermenting"
    AGING = "aging"
    BOTTLED = "bottled"
    RELEASED = "released"

class Vineyard(Base):
    __tablename__ = "vineyards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # location: GeoJSON. Using Geometry type from geoalchemy2
    location = Column(Geometry("POLYGON"), nullable=True)
    area_hectares = Column(Float, nullable=False)
    grape_varieties = Column(JSON, nullable=False)  # JSON field
    soil_type = Column(String, nullable=True)
    elevation_m = Column(Float, nullable=True)
    climate_zone = Column(String, nullable=True)
    organic_certified = Column(Boolean, default=False)

    harvest_batches = relationship("HarvestBatch", back_populates="vineyard")


class HarvestBatch(Base):
    __tablename__ = "harvest_batches"

    id = Column(Integer, primary_key=True, index=True)
    vineyard_id = Column(Integer, ForeignKey("vineyards.id"), nullable=False)
    variety = Column(String, nullable=False)
    harvest_date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=False)
    brix_level = Column(Float, nullable=False)
    ph = Column(Float, nullable=False)
    acidity = Column(Float, nullable=False)
    quality_grade = Column(SAEnum(QualityGrade), nullable=False)
    destination_tank_id = Column(String, nullable=True)

    vineyard = relationship("Vineyard", back_populates="harvest_batches")


class WineLot(Base):
    __tablename__ = "wine_lots"

    id = Column(Integer, primary_key=True, index=True)
    batch_ids = Column(JSON, nullable=False)  # List of batch IDs
    wine_type = Column(SAEnum(WineType), nullable=False)
    fermentation_start = Column(DateTime, nullable=True)
    fermentation_end = Column(DateTime, nullable=True)
    aging_vessel = Column(SAEnum(AgingVessel), nullable=True)
    volume_liters = Column(Float, nullable=False)
    status = Column(SAEnum(WineStatus), default=WineStatus.FERMENTING)
