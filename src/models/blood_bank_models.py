from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
import enum
from datetime import date, datetime
from src.database import Base

class BloodType(str, enum.Enum):
    A_POS = "A_pos"
    A_NEG = "A_neg"
    B_POS = "B_pos"
    B_NEG = "B_neg"
    AB_POS = "AB_pos"
    AB_NEG = "AB_neg"
    O_POS = "O_pos"
    O_NEG = "O_neg"

class BloodComponent(str, enum.Enum):
    WHOLE_BLOOD = "whole_blood"
    RBC = "rbc"
    PLASMA = "plasma"
    PLATELETS = "platelets"

class BloodUnitStatus(str, enum.Enum):
    COLLECTED = "collected"
    TESTED = "tested"
    AVAILABLE = "available"
    RESERVED = "reserved"
    TRANSFUSED = "transfused"
    EXPIRED = "expired"

class UrgencyLevel(str, enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class RequestStatus(str, enum.Enum):
    REQUESTED = "requested"
    MATCHED = "matched"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"

class CrossmatchStatus(str, enum.Enum):
    PENDING = "pending"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"

class Donor(Base):
    __tablename__ = "donors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType), index=True)
    last_donation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_donations: Mapped[int] = mapped_column(Integer, default=0)
    eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    deferral_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    donations: Mapped[List["BloodUnit"]] = relationship("BloodUnit", back_populates="donor", lazy="selectin")

class BloodUnit(Base):
    __tablename__ = "blood_units"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    donor_id: Mapped[int] = mapped_column(ForeignKey("donors.id"))
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType), index=True)
    component: Mapped[BloodComponent] = mapped_column(SAEnum(BloodComponent), index=True)
    collection_date: Mapped[date] = mapped_column(Date)
    expiry_date: Mapped[date] = mapped_column(Date)
    volume_ml: Mapped[int] = mapped_column(Integer)
    status: Mapped[BloodUnitStatus] = mapped_column(SAEnum(BloodUnitStatus), default=BloodUnitStatus.COLLECTED, index=True)
    storage_location: Mapped[str] = mapped_column(String)

    donor: Mapped["Donor"] = relationship("Donor", back_populates="donations")

class TransfusionRequest(Base):
    __tablename__ = "transfusion_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    hospital_id: Mapped[str] = mapped_column(String, index=True)
    blood_type: Mapped[BloodType] = mapped_column(SAEnum(BloodType))
    component: Mapped[BloodComponent] = mapped_column(SAEnum(BloodComponent))
    units_needed: Mapped[int] = mapped_column(Integer)
    urgency: Mapped[UrgencyLevel] = mapped_column(SAEnum(UrgencyLevel), default=UrgencyLevel.ROUTINE)
    crossmatch_status: Mapped[CrossmatchStatus] = mapped_column(SAEnum(CrossmatchStatus), default=CrossmatchStatus.PENDING)
    status: Mapped[RequestStatus] = mapped_column(SAEnum(RequestStatus), default=RequestStatus.REQUESTED, index=True)
