from enum import Enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Standard(str, Enum):
    VERRA = "verra"
    GOLD_STANDARD = "gold_standard"
    CDM = "cdm"

class CreditType(str, Enum):
    AVOIDANCE = "avoidance"
    REMOVAL = "removal"

class CreditStatus(str, Enum):
    ISSUED = "issued"
    TRADED = "traded"
    RETIRED = "retired"

class ProjectType(str, Enum):
    FORESTRY = "forestry"
    RENEWABLE = "renewable"
    METHANE = "methane"

class TradeStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    SETTLED = "settled"

class CarbonProject(Base):
    __tablename__ = "carbon_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    methodology: Mapped[str] = mapped_column(String, nullable=False)
    project_type: Mapped[ProjectType] = mapped_column(SQLEnum(ProjectType), nullable=False)
    annual_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    verification_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registry_url: Mapped[str] = mapped_column(String, nullable=True)

    credits = relationship("CarbonCredit", back_populates="project")

class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("carbon_projects.id"), nullable=False)
    vintage_year: Mapped[int] = mapped_column(Integer, nullable=False)
    standard: Mapped[Standard] = mapped_column(SQLEnum(Standard), nullable=False)
    credit_type: Mapped[CreditType] = mapped_column(SQLEnum(CreditType), nullable=False)
    tonnes_co2: Mapped[float] = mapped_column(Float, nullable=False)
    serial_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[CreditStatus] = mapped_column(SQLEnum(CreditStatus), default=CreditStatus.ISSUED, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, nullable=False)

    project = relationship("CarbonProject", back_populates="credits")

class TradeOrder(Base):
    __tablename__ = "trade_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[str] = mapped_column(String, nullable=True)
    seller_id: Mapped[str] = mapped_column(String, nullable=False)
    credit_id: Mapped[int] = mapped_column(ForeignKey("carbon_credits.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_tonne: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    status: Mapped[TradeStatus] = mapped_column(SQLEnum(TradeStatus), default=TradeStatus.PENDING, nullable=False)
    traded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
