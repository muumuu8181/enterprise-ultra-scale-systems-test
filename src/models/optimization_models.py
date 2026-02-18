from sqlalchemy import Column, Integer, String, Float, JSON, Enum as SAEnum, DateTime
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
import enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

Base = declarative_base()

class EnforcementType(str, enum.Enum):
    WARN = "warn"
    BLOCK = "block"

class ReservedInstance(Base):
    __tablename__ = "reserved_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String)
    instance_type: Mapped[str] = mapped_column(String)
    region: Mapped[str] = mapped_column(String)
    term_months: Mapped[int] = mapped_column(Integer)
    upfront_cost: Mapped[float] = mapped_column(Float)
    monthly_savings: Mapped[float] = mapped_column(Float)
    utilization_pct: Mapped[float] = mapped_column(Float)

class TaggingPolicy(Base):
    __tablename__ = "tagging_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[str] = mapped_column(String, index=True)
    required_tags: Mapped[dict] = mapped_column(JSON)
    enforcement: Mapped[EnforcementType] = mapped_column(SAEnum(EnforcementType))
    compliance_score: Mapped[float] = mapped_column(Float)

class CarbonFootprint(Base):
    __tablename__ = "carbon_footprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[str] = mapped_column(String, index=True)
    period: Mapped[str] = mapped_column(String) # e.g. "2023-10"
    co2e_tonnes: Mapped[float] = mapped_column(Float)
    renewable_pct: Mapped[float] = mapped_column(Float)
    efficiency_score: Mapped[float] = mapped_column(Float)
    region_breakdown: Mapped[dict] = mapped_column(JSON)

# Pydantic Models for API/Service

class ReservationDeal(BaseModel):
    provider: str
    instance_type: str
    region: str
    term_months: int
    upfront_cost: float
    monthly_savings: float
    estimated_utilization_pct: float

    model_config = ConfigDict(from_attributes=True)

class TaggingReport(BaseModel):
    account_id: str
    compliance_score: float
    non_compliant_resources: List[Dict[str, Any]]
    enforced_actions: List[str]

    model_config = ConfigDict(from_attributes=True)

class CarbonFootprintSchema(BaseModel):
    account_id: str
    period: str
    co2e_tonnes: float
    renewable_pct: float
    efficiency_score: float
    region_breakdown: Dict[str, float]

    model_config = ConfigDict(from_attributes=True)

class ReductionRoadmap(BaseModel):
    current_emission: float
    target_emission: float
    steps: List[str]
    estimated_completion_date: str
