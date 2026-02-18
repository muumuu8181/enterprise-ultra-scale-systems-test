from sqlalchemy import Integer, String, Float, JSON, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timezone
import enum
from typing import List, Optional, Any

class Base(DeclarativeBase):
    pass

class ConsultationType(str, enum.Enum):
    VIDEO = "video"
    CHAT = "chat"
    PHONE = "phone"

class ConsultationStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True)
    specialty: Mapped[str] = mapped_column(String)
    medical_license: Mapped[str] = mapped_column(String)
    consultation_fee: Mapped[float] = mapped_column(Float)
    available_slots: Mapped[List[Any]] = mapped_column(JSON) # e.g. [{"start": "...", "end": "..."}]
    languages: Mapped[List[str]] = mapped_column(JSON)
    rating: Mapped[float] = mapped_column(Float)

    consultations: Mapped[List["Consultation"]] = relationship(back_populates="doctor")

class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(Integer)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id"))
    consultation_type: Mapped[ConsultationType] = mapped_column(SAEnum(ConsultationType))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[ConsultationStatus] = mapped_column(SAEnum(ConsultationStatus), default=ConsultationStatus.SCHEDULED)
    chief_complaint: Mapped[str] = mapped_column(String)
    duration_min: Mapped[int] = mapped_column(Integer)

    doctor: Mapped["Doctor"] = relationship(back_populates="consultations")
    prescriptions: Mapped[List["Prescription"]] = relationship(back_populates="consultation")

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consultation_id: Mapped[int] = mapped_column(Integer, ForeignKey("consultations.id"))
    medications: Mapped[List[Any]] = mapped_column(JSON)
    dosage_instructions: Mapped[str] = mapped_column(String)
    refills_allowed: Mapped[int] = mapped_column(Integer)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    pharmacy_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    consultation: Mapped["Consultation"] = relationship(back_populates="prescriptions")
