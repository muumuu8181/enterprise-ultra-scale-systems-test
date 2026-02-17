from sqlalchemy import Column, Integer, String, Text, Date, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from src.database import Base

class PatentStatus(str, enum.Enum):
    PROVISIONAL = "provisional"
    PENDING = "pending"
    GRANTED = "granted"
    EXPIRED = "expired"
    ABANDONED = "abandoned"

class ClaimType(str, enum.Enum):
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"

class CitationType(str, enum.Enum):
    EXAMINER = "examiner"
    APPLICANT = "applicant"

class Relevance(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    X = "X"
    Y = "Y"

class Patent(Base):
    __tablename__ = "patents"

    id = Column(Integer, primary_key=True, index=True)
    patent_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    abstract = Column(Text)
    inventors = Column(JSON)
    assignee_id = Column(String, index=True)
    filing_date = Column(Date)
    grant_date = Column(Date)
    expiry_date = Column(Date)
    jurisdiction = Column(String)
    classification = Column(JSON)
    status = Column(Enum(PatentStatus), nullable=False)

    claims = relationship("Claim", back_populates="patent")
    # Citations where this patent is the citing one (forward looking from this patent to others)
    # Wait, 'forward' usually means patents that cite THIS patent.
    # 'backward' usually means patents THIS patent cites.

    # Let's define relationships carefully.
    # cited_by: patents that cite this patent (forward citations)
    # cites: patents that this patent cites (backward citations)

    citations_made = relationship("Citation", foreign_keys="Citation.citing_patent_id", back_populates="citing_patent")
    citations_received = relationship("Citation", foreign_keys="Citation.cited_patent_id", back_populates="cited_patent")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    patent_id = Column(Integer, ForeignKey("patents.id"), nullable=False)
    claim_number = Column(Integer, nullable=False)
    claim_type = Column(Enum(ClaimType), nullable=False)
    depends_on = Column(Integer, nullable=True) # Could refer to another claim number or ID. Usually claim number within the patent.
    text = Column(Text, nullable=False)
    scope_keywords = Column(JSON)

    patent = relationship("Patent", back_populates="claims")

class Citation(Base):
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    citing_patent_id = Column(Integer, ForeignKey("patents.id"), nullable=False)
    cited_patent_id = Column(Integer, ForeignKey("patents.id"), nullable=False)
    citation_type = Column(Enum(CitationType), nullable=False)
    relevance = Column(Enum(Relevance))
    cited_text = Column(Text)

    citing_patent = relationship("Patent", foreign_keys=[citing_patent_id], back_populates="citations_made")
    cited_patent = relationship("Patent", foreign_keys=[cited_patent_id], back_populates="citations_received")
