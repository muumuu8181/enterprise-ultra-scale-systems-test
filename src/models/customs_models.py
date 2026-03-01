from sqlalchemy import Column, Integer, String, Enum, JSON, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
import enum
from datetime import datetime

class DeclarationType(str, enum.Enum):
    IMPORT = "import"
    EXPORT = "export"
    TRANSIT = "transit"

class DeclarationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ASSESSED = "assessed"
    CLEARED = "cleared"
    REJECTED = "rejected"

class InspectionType(str, enum.Enum):
    DOCUMENT = "document"
    PHYSICAL = "physical"
    SCANNER = "scanner"

class InspectionResult(str, enum.Enum):
    CLEAR = "clear"
    HOLD = "hold"
    SEIZE = "seize"
    PENDING = "pending"  # Added pending as a default before completion

class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String, unique=True, index=True, nullable=False)
    declaration_type = Column(Enum(DeclarationType), nullable=False)
    trader_id = Column(String, index=True, nullable=False)
    country_origin = Column(String, nullable=False)
    country_dest = Column(String, nullable=False)
    goods = Column(JSON, nullable=False)  # List of items
    total_value = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(Enum(DeclarationStatus), default=DeclarationStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inspections = relationship("Inspection", back_populates="declaration")

class TariffCode(Base):
    __tablename__ = "tariff_codes"

    id = Column(Integer, primary_key=True, index=True)
    hs_code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    duty_rate_pct = Column(Float, nullable=False)
    vat_rate_pct = Column(Float, nullable=False)
    restrictions = Column(JSON, default=list)
    preferential_agreements = Column(JSON, default=dict)
    effective_date = Column(DateTime, nullable=False)

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    declaration_id = Column(Integer, ForeignKey("declarations.id"), nullable=False)
    inspection_type = Column(Enum(InspectionType), nullable=False)
    assigned_officer_id = Column(String, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    result = Column(Enum(InspectionResult), default=InspectionResult.PENDING, nullable=True)
    findings = Column(String, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    declaration = relationship("Declaration", back_populates="inspections")
