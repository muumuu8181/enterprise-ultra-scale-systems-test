from enum import Enum
from datetime import date, datetime
from typing import Any, Dict
from sqlalchemy import Integer, String, Float, Date, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from geoalchemy2 import Geometry

class Base(DeclarativeBase):
    pass

class CertificationType(str, Enum):
    FSC = "fsc"
    PEFC = "pefc"
    NONE = "none"

class HarvestType(str, Enum):
    CLEARCUT = "clearcut"
    SELECTIVE = "selective"
    THINNING = "thinning"

class HarvestStatus(str, Enum):
    PLANNED = "planned"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"

class LogGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class ForestPlot(Base):
    __tablename__ = "forest_plots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    # GeoJSON location, assuming Polygon for a plot area
    location: Mapped[Any] = mapped_column(Geometry("POLYGON"))
    area_hectares: Mapped[float] = mapped_column(Float)
    species_composition: Mapped[Dict[str, Any]] = mapped_column(JSON)
    age_class: Mapped[str] = mapped_column(String)
    volume_m3_ha: Mapped[float] = mapped_column(Float)
    last_inventory_date: Mapped[date] = mapped_column(Date)
    certification: Mapped[CertificationType] = mapped_column(SAEnum(CertificationType))
    owner_id: Mapped[int] = mapped_column(Integer)

class HarvestPlan(Base):
    __tablename__ = "harvest_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plot_id: Mapped[int] = mapped_column(ForeignKey("forest_plots.id"))
    harvest_type: Mapped[HarvestType] = mapped_column(SAEnum(HarvestType))
    volume_target_m3: Mapped[float] = mapped_column(Float)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    contractor_id: Mapped[int] = mapped_column(Integer)
    environmental_assessment: Mapped[str] = mapped_column(String)
    status: Mapped[HarvestStatus] = mapped_column(SAEnum(HarvestStatus))

class LogBatch(Base):
    __tablename__ = "log_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    harvest_id: Mapped[int] = mapped_column(ForeignKey("harvest_plans.id"))
    species: Mapped[str] = mapped_column(String)
    grade: Mapped[LogGrade] = mapped_column(SAEnum(LogGrade))
    volume_m3: Mapped[float] = mapped_column(Float)
    destination_mill: Mapped[str] = mapped_column(String)
    transport_method: Mapped[str] = mapped_column(String)
    chain_of_custody_cert: Mapped[str] = mapped_column(String)
    dispatched_at: Mapped[datetime] = mapped_column(DateTime)
