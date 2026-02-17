from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from datetime import datetime, timezone
from typing import Optional

class Medication(Base):
    """
    医薬品モデル
    """
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    generic_name: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    dosage_form: Mapped[str] = mapped_column(String)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=10)

class Dispensing(Base):
    """
    調剤記録モデル
    """
    __tablename__ = "dispensings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prescription_id: Mapped[int] = mapped_column(Integer, index=True)
    # medication_id is not in the prompt, so we won't add it as a column,
    # but in a real app it would be essential.
    # We assume prescription_id links to a Prescription which links to Medication.

    pharmacist_id: Mapped[int] = mapped_column(Integer)
    dispensed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    quantity: Mapped[int] = mapped_column(Integer)
    batch_number: Mapped[str] = mapped_column(String)
