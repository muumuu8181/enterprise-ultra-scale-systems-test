from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import enum
from src.database import Base

class CaseType(str, enum.Enum):
    CIVIL = "civil"
    CRIMINAL = "criminal"
    FAMILY = "family"
    BANKRUPTCY = "bankruptcy"
    APPELLATE = "appellate"

class CaseStatus(str, enum.Enum):
    FILED = "filed"
    DISCOVERY = "discovery"
    TRIAL = "trial"
    VERDICT = "verdict"
    APPEAL = "appeal"
    CLOSED = "closed"

class HearingType(str, enum.Enum):
    ARRAIGNMENT = "arraignment"
    PRETRIAL = "pretrial"
    TRIAL = "trial"
    SENTENCING = "sentencing"
    MOTION = "motion"

class HearingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CONTINUED = "continued"
    CANCELLED = "cancelled"

class DocType(str, enum.Enum):
    COMPLAINT = "complaint"
    MOTION = "motion"
    BRIEF = "brief"
    ORDER = "order"
    VERDICT = "verdict"

class DocStatus(str, enum.Enum):
    FILED = "filed"
    SERVED = "served"
    UNDER_REVIEW = "under_review"

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_number: Mapped[str] = mapped_column(unique=True, index=True)
    case_type: Mapped[CaseType] = mapped_column(Enum(CaseType))
    plaintiff: Mapped[str] = mapped_column(String)
    defendant: Mapped[str] = mapped_column(String)
    judge_id: Mapped[int] = mapped_column(Integer)
    filed_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.FILED)
    court_id: Mapped[int] = mapped_column(Integer)

    hearings = relationship("Hearing", back_populates="case")
    documents = relationship("Document", back_populates="case")

class Hearing(Base):
    __tablename__ = "hearings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    hearing_type: Mapped[HearingType] = mapped_column(Enum(HearingType))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    courtroom: Mapped[str] = mapped_column(String)
    judge_id: Mapped[int] = mapped_column(Integer)
    duration_min: Mapped[int] = mapped_column(Integer)
    status: Mapped[HearingStatus] = mapped_column(Enum(HearingStatus), default=HearingStatus.SCHEDULED)

    case = relationship("Case", back_populates="hearings")

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType))
    filed_by: Mapped[str] = mapped_column(String)
    filed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    description: Mapped[str] = mapped_column(String, nullable=True)
    file_url: Mapped[str] = mapped_column(String)
    sealed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[DocStatus] = mapped_column(Enum(DocStatus), default=DocStatus.FILED)

    case = relationship("Case", back_populates="documents")
