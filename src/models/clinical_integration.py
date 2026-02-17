from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from datetime import datetime

class ClinicalExport(Base):
    """
    Clinical Export Model
    """
    __tablename__ = "clinical_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    format: Mapped[str] = mapped_column(String) # fhir_r4/hl7/csv
    requested_by: Mapped[str] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    file_path: Mapped[str] = mapped_column(String)

class HealthGoal(Base):
    """
    Health Goal Model
    """
    __tablename__ = "health_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    goal_type: Mapped[str] = mapped_column(String) # weight/steps/sleep/glucose
    target_value: Mapped[float] = mapped_column(Float)
    deadline: Mapped[datetime] = mapped_column(DateTime)
    current_progress: Mapped[float] = mapped_column(Float, default=0.0)

class PrescriptionAlert(Base):
    """
    Prescription Alert Model
    """
    __tablename__ = "prescription_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    medication: Mapped[str] = mapped_column(String)
    missed_dose_at: Mapped[datetime] = mapped_column(DateTime)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
