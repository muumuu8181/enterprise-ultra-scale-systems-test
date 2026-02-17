from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from datetime import datetime, timezone
from src.database import Base

class MedicationForm(str, enum.Enum):
    tablet = "tablet"
    capsule = "capsule"
    liquid = "liquid"
    injection = "injection"

class PrescriptionStatus(str, enum.Enum):
    received = "received"
    verified = "verified"
    filled = "filled"
    picked_up = "picked_up"
    cancelled = "cancelled"

class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    generic_name: Mapped[str] = mapped_column(String)
    ndc_code: Mapped[str] = mapped_column(String, unique=True, index=True)
    drug_class: Mapped[str] = mapped_column(String, index=True)
    form: Mapped[MedicationForm] = mapped_column(SAEnum(MedicationForm))
    strength: Mapped[str] = mapped_column(String)
    manufacturer: Mapped[str] = mapped_column(String)
    requires_rx: Mapped[bool] = mapped_column(Boolean, default=True)
    controlled_schedule: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=10)

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    prescriber_id: Mapped[str] = mapped_column(String, index=True)
    medication_id: Mapped[str] = mapped_column(ForeignKey("medications.id"))
    dosage: Mapped[str] = mapped_column(String)
    frequency: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    refills_allowed: Mapped[int] = mapped_column(Integer, default=0)
    refills_used: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PrescriptionStatus] = mapped_column(SAEnum(PrescriptionStatus), default=PrescriptionStatus.received)
    rx_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    medication = relationship("Medication")

class Dispensing(Base):
    __tablename__ = "dispensings"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    prescription_id: Mapped[str] = mapped_column(ForeignKey("prescriptions.id"))
    pharmacist_id: Mapped[str] = mapped_column(String)
    dispensed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    quantity: Mapped[int] = mapped_column(Integer)
    lot_number: Mapped[str] = mapped_column(String)
    expiry_date: Mapped[datetime] = mapped_column(DateTime)
    patient_counseled: Mapped[bool] = mapped_column(Boolean, default=False)
    copay_amount: Mapped[float] = mapped_column(Float)

    prescription = relationship("Prescription")
