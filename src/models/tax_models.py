from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.database import Base

class EntityType(str, enum.Enum):
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    PARTNERSHIP = "partnership"

class TaxType(str, enum.Enum):
    INCOME = "income"
    VAT = "vat"
    PAYROLL = "payroll"
    WITHHOLDING = "withholding"

class FilingStatus(str, enum.Enum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    FILED = "filed"
    ACCEPTED = "accepted"
    AMENDED = "amended"

class TaxEntity(Base):
    __tablename__ = "tax_entities"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(SAEnum(EntityType), nullable=False)
    tax_id = Column(String, unique=True, index=True, nullable=False)
    jurisdiction = Column(String, nullable=False)
    fiscal_year_end = Column(Date, nullable=False)
    filing_status = Column(String, nullable=True) # e.g. "active", "suspended", or frequency "monthly"
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

    filings = relationship("TaxFiling", back_populates="entity")

class TaxFiling(Base):
    __tablename__ = "tax_filings"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("tax_entities.id"), nullable=False)
    tax_type = Column(SAEnum(TaxType), nullable=False)
    period = Column(String, nullable=False) # e.g. "2023-Q1", "2023"
    gross_income = Column(Float, default=0.0)
    deductions = Column(JSON, default={})
    tax_liability = Column(Float, default=0.0)
    status = Column(SAEnum(FilingStatus), default=FilingStatus.DRAFT)
    due_date = Column(Date, nullable=False)

    entity = relationship("TaxEntity", back_populates="filings")

class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String, nullable=False)
    tax_type = Column(SAEnum(TaxType), nullable=False)
    effective_date = Column(Date, nullable=False)
    rate_pct = Column(Float, nullable=False)
    brackets = Column(JSON, nullable=True) # e.g. [{"limit": 10000, "rate": 0.1}, ...]
    exemptions = Column(JSON, default={})
    active = Column(Boolean, default=True)
