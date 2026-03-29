from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database import Base
import enum
from datetime import date
from typing import List, Optional

class ArtifactCondition(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class ExhibitionStatus(str, enum.Enum):
    PLANNING = "planning"
    INSTALLING = "installing"
    OPEN = "open"
    CLOSED = "closed"

class LoanStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    ACTIVE = "active"
    RETURNED = "returned"

class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    accession_number: Mapped[str] = mapped_column(unique=True, index=True)
    title: Mapped[str]
    artist_creator: Mapped[str]
    period: Mapped[str] = mapped_column(index=True)
    medium: Mapped[str] = mapped_column(index=True)
    dimensions: Mapped[str]
    provenance: Mapped[List[dict]] = mapped_column(JSON, default=list) # Provenance history
    location_gallery: Mapped[str]
    condition: Mapped[ArtifactCondition]
    insurance_value: Mapped[float]

    loans: Mapped[List["LoanAgreement"]] = relationship(back_populates="artifact")
    conservation_logs: Mapped[List["ConservationLog"]] = relationship(back_populates="artifact")

class Exhibition(Base):
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    curator_id: Mapped[int] # Assuming just an ID for now
    theme: Mapped[str]
    start_date: Mapped[date]
    end_date: Mapped[date]
    galleries: Mapped[List[str]] = mapped_column(JSON, default=list)
    artifact_ids: Mapped[List[int]] = mapped_column(JSON, default=list) # List of artifact IDs included
    status: Mapped[ExhibitionStatus] = mapped_column(default=ExhibitionStatus.PLANNING)
    visitor_count: Mapped[int] = mapped_column(default=0)

class LoanAgreement(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id"))
    borrower_institution: Mapped[str]
    purpose: Mapped[str]
    loan_start: Mapped[date]
    loan_end: Mapped[date]
    insurance_amount: Mapped[float]
    condition_report_url: Mapped[Optional[str]] = mapped_column(default=None)
    status: Mapped[LoanStatus] = mapped_column(default=LoanStatus.REQUESTED)

    artifact: Mapped["Artifact"] = relationship(back_populates="loans")

class ConservationLog(Base):
    __tablename__ = "conservation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id"))
    log_date: Mapped[date]
    description: Mapped[str]
    reporter: Mapped[str]

    artifact: Mapped["Artifact"] = relationship(back_populates="conservation_logs")
