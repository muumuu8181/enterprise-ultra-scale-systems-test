from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Enum, Float, Text, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

# Assuming Base is defined elsewhere, but for now defining it here to avoid dependency issues.
# In a real project, this would likely be imported from src.db.base.
Base = declarative_base()

class DocType(str, enum.Enum):
    CONTRACT = "contract"
    NDA = "nda"
    PATENT = "patent"
    LITIGATION = "litigation"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class LegalDocument(Base):
    __tablename__ = 'legal_documents'
    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(Enum(DocType), nullable=False)
    title = Column(String, nullable=False)
    parties = Column(JSON, nullable=True)
    status = Column(String, default="draft")
    file_path = Column(String, nullable=True)
    extracted_clauses = Column(JSON, nullable=True)

    contract = relationship("Contract", back_populates="document", uselist=False)

class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('legal_documents.id'), nullable=False)
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    obligations = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=True)
    review_status = Column(String, default="pending")

    document = relationship("LegalDocument", back_populates="contract")
    clauses = relationship("Clause", back_populates="contract")

class Clause(Base):
    __tablename__ = 'clauses'
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    clause_type = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    is_standard = Column(Boolean, default=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    suggested_revision = Column(Text, nullable=True)

    contract = relationship("Contract", back_populates="clauses")
