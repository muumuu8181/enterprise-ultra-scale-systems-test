from sqlalchemy import String, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
import enum

class Framework(str, enum.Enum):
    BASEL3 = "basel3"
    SOLVENCY2 = "solvency2"

class Counterparty(Base):
    __tablename__ = "counterparties"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    credit_rating: Mapped[str] = mapped_column(String)
    pd_estimate: Mapped[float] = mapped_column(Float)  # Probability of Default
    lgd_estimate: Mapped[float] = mapped_column(Float) # Loss Given Default
    ead: Mapped[float] = mapped_column(Float)          # Exposure at Default
    industry: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)

    exposures: Mapped[list["CreditExposure"]] = relationship(back_populates="counterparty")

class CreditExposure(Base):
    __tablename__ = "credit_exposures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    portfolio_id: Mapped[str] = mapped_column(String, index=True)
    counterparty_id: Mapped[int] = mapped_column(ForeignKey("counterparties.id"))
    exposure_type: Mapped[str] = mapped_column(String)
    nominal: Mapped[float] = mapped_column(Float)
    mtm_value: Mapped[float] = mapped_column(Float) # Mark-to-Market
    collateral: Mapped[float] = mapped_column(Float)

    counterparty: Mapped["Counterparty"] = relationship(back_populates="exposures")

class RegulatoryCapital(Base):
    __tablename__ = "regulatory_capital"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[str] = mapped_column(String, index=True)
    framework: Mapped[Framework] = mapped_column(SAEnum(Framework))
    tier1_capital: Mapped[float] = mapped_column(Float)
    rwa: Mapped[float] = mapped_column(Float) # Risk Weighted Assets
    capital_ratio: Mapped[float] = mapped_column(Float)
