from enum import Enum as PyEnum
from sqlalchemy import Integer, String, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base

class EmissionSourceType(str, PyEnum):
    INDUSTRIAL = "industrial"
    TRANSPORT = "transport"
    AGRICULTURE = "agriculture"

class EmissionScope(int, PyEnum):
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3

class CreditStatus(str, PyEnum):
    ISSUED = "issued"
    RETIRED = "retired"
    CANCELLED = "cancelled"

class EmissionSource(Base):
    __tablename__ = "emission_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_id: Mapped[str] = mapped_column(String, index=True)
    source_type: Mapped[EmissionSourceType] = mapped_column(SQLEnum(EmissionSourceType))
    scope: Mapped[EmissionScope] = mapped_column(SQLEnum(EmissionScope))
    reported_co2_kt: Mapped[float] = mapped_column(Float)

class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String, index=True)
    vintage_year: Mapped[int] = mapped_column(Integer)
    volume_tco2: Mapped[float] = mapped_column(Float)
    status: Mapped[CreditStatus] = mapped_column(SQLEnum(CreditStatus))
    registry: Mapped[str] = mapped_column(String)

class NetZeroTarget(Base):
    __tablename__ = "net_zero_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_id: Mapped[str] = mapped_column(String, index=True)
    baseline_year: Mapped[int] = mapped_column(Integer)
    target_year: Mapped[int] = mapped_column(Integer)
    reduction_pct: Mapped[float] = mapped_column(Float)
    current_progress: Mapped[float] = mapped_column(Float)
