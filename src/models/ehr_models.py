from sqlalchemy import Column, Integer, String, Boolean, JSON, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import enum

class LabStatus(str, enum.Enum):
    ordered = "ordered"
    collected = "collected"
    resulted = "resulted"

class ReferralUrgency(str, enum.Enum):
    routine = "routine"
    urgent = "urgent"
    emergency = "emergency"

class PatientRecord(Base):
    __tablename__ = "patient_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    allergies: Mapped[dict] = mapped_column(JSON, default={})
    chronic_conditions: Mapped[dict] = mapped_column(JSON, default={})
    medications: Mapped[dict] = mapped_column(JSON, default={})
    blood_type: Mapped[str] = mapped_column(String, nullable=True)
    emergency_contact: Mapped[str] = mapped_column(String, nullable=True)

class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    consultation_id: Mapped[str] = mapped_column(String, index=True)
    tests: Mapped[dict] = mapped_column(JSON, default={})
    lab_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[LabStatus] = mapped_column(SAEnum(LabStatus), default=LabStatus.ordered)
    results_uri: Mapped[str] = mapped_column(String, nullable=True)

class ReferralLetter(Base):
    __tablename__ = "referral_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)  # Added for security filtering
    consultation_id: Mapped[str] = mapped_column(String, index=True)
    referred_to_specialty: Mapped[str] = mapped_column(String)
    urgency: Mapped[ReferralUrgency] = mapped_column(SAEnum(ReferralUrgency), default=ReferralUrgency.routine)
    clinical_summary: Mapped[str] = mapped_column(Text)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
