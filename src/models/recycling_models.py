from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from geoalchemy2 import Geometry
import enum
from datetime import datetime
from src.database import Base

class PointType(enum.Enum):
    curbside = "curbside"
    drop_off = "drop_off"
    commercial = "commercial"

class MaterialType(enum.Enum):
    paper = "paper"
    plastic = "plastic"
    glass = "glass"
    metal = "metal"
    ewaste = "ewaste"
    organic = "organic"

class BatchStatus(enum.Enum):
    collected = "collected"
    sorted = "sorted"
    processed = "processed"
    sold = "sold"

class MarketGrade(enum.Enum):
    A = "A"
    B = "B"
    C = "C"

class PriceTrend(enum.Enum):
    up = "up"
    stable = "stable"
    down = "down"

class CollectionPoint(Base):
    __tablename__ = "collection_points"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(Geometry('POINT'))
    point_type = Column(Enum(PointType))
    materials_accepted = Column(JSON)
    capacity_kg = Column(Float)
    fill_level_pct = Column(Float)
    next_pickup = Column(DateTime)

class RecyclingBatch(Base):
    __tablename__ = "recycling_batches"

    id = Column(Integer, primary_key=True, index=True)
    collection_point_id = Column(Integer, ForeignKey("collection_points.id"))
    material = Column(Enum(MaterialType))
    weight_kg = Column(Float)
    contamination_pct = Column(Float)
    sorted_at = Column(DateTime, nullable=True)
    destination_facility_id = Column(Integer)
    status = Column(Enum(BatchStatus), default=BatchStatus.collected)

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    material = Column(Enum(MaterialType))
    grade = Column(Enum(MarketGrade))
    price_per_kg = Column(Float)
    currency = Column(String)
    region = Column(String)
    effective_date = Column(DateTime, default=datetime.utcnow)
    trend = Column(Enum(PriceTrend))
