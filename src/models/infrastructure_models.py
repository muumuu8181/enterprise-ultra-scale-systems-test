from enum import Enum as PyEnum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class AssetType(str, PyEnum):
    ROAD = "road"
    BRIDGE = "bridge"
    UTILITY = "utility"
    TRANSIT = "transit"

class MaintenanceType(str, PyEnum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"

class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    name = Column(String, nullable=False)
    condition_score = Column(Float, nullable=False)
    last_inspection = Column(DateTime, nullable=True)
    replacement_value = Column(Float, nullable=False)

class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("infrastructure_assets.id"), nullable=False)
    maintenance_type = Column(Enum(MaintenanceType), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    cost_estimate = Column(Float, nullable=False)
    priority = Column(Integer, nullable=False)

class TrafficFlow(Base):
    __tablename__ = "traffic_flows"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    vehicle_count = Column(Integer, nullable=False)
    avg_speed = Column(Float, nullable=False)
    congestion_level = Column(Float, nullable=False)

# Pydantic Models for Service Returns
class MaintenancePrediction(BaseModel):
    asset_id: int
    predicted_failure_date: datetime
    confidence_score: float
    recommended_action: str

class TrafficSimResult(BaseModel):
    simulation_id: str
    impact_score: float
    affected_segments: List[int]
    estimated_delay_minutes: float
