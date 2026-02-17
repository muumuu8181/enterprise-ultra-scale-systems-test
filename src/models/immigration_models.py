from enum import Enum
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class VisaType(str, Enum):
    TOURIST = "tourist"
    WORK = "work"
    STUDENT = "student"
    FAMILY = "family"
    REFUGEE = "refugee"

class ApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    DOCUMENTS_REVIEW = "documents_review"
    INTERVIEW = "interview"
    APPROVED = "approved"
    DENIED = "denied"

class BackgroundCheckStatus(str, Enum):
    PENDING = "pending"
    CLEAR = "clear"
    FLAGGED = "flagged"

class EntryStatus(str, Enum):
    ADMITTED = "admitted"
    SECONDARY_INSPECTION = "secondary_inspection"
    DENIED_ENTRY = "denied_entry"

class Applicant(Base):
    __tablename__ = 'applicants'

    id = Column(Integer, primary_key=True, index=True)
    passport_number = Column(String, unique=True, index=True, nullable=False)
    nationality = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    biometrics_collected = Column(Boolean, default=False)
    background_check_status = Column(SQLEnum(BackgroundCheckStatus), default=BackgroundCheckStatus.PENDING)
    travel_history = Column(JSON, default=list)

    applications = relationship("VisaApplication", back_populates="applicant")
    border_entries = relationship("BorderEntry", back_populates="applicant")

class VisaApplication(Base):
    __tablename__ = 'visa_applications'

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey('applicants.id'), nullable=False)
    visa_type = Column(SQLEnum(VisaType), nullable=False)
    destination_country = Column(String, nullable=False)
    embassy_id = Column(String, nullable=False)
    submission_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    interview_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.SUBMITTED)
    processing_time_days = Column(Integer, nullable=True)

    applicant = relationship("Applicant", back_populates="applications")
    border_entries = relationship("BorderEntry", back_populates="visa")

class BorderEntry(Base):
    __tablename__ = 'border_entries'

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey('applicants.id'), nullable=False)
    port_of_entry = Column(String, nullable=False)
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    visa_id = Column(Integer, ForeignKey('visa_applications.id'), nullable=True)
    customs_declaration = Column(JSON, default=dict)
    biometric_verified = Column(Boolean, default=False)
    status = Column(SQLEnum(EntryStatus), default=EntryStatus.ADMITTED)

    applicant = relationship("Applicant", back_populates="border_entries")
    visa = relationship("VisaApplication", back_populates="border_entries")
