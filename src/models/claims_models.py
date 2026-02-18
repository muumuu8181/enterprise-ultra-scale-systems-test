from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class DocType(str, enum.Enum):
    photo = "photo"
    medical = "medical"
    police = "police"

class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, index=True)
    # Placeholder for other claim fields

class ClaimDocument(Base):
    __tablename__ = "claim_documents"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    doc_type = Column(Enum(DocType))
    file_path = Column(String)
    verified = Column(Boolean, default=False)
    ocr_extracted = Column(JSON)

    claim = relationship("Claim")

class FraudFlag(Base):
    __tablename__ = "fraud_flags"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    rule_triggered = Column(String)
    risk_score = Column(Float)
    analyst_decision = Column(String)

    claim = relationship("Claim")

class Reinsurance(Base):
    __tablename__ = "reinsurance"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    treaty_id = Column(String)
    ceded_amount = Column(Float)
    recovery_amount = Column(Float)

    claim = relationship("Claim")
