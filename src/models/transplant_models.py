from typing import Any, Dict
from datetime import datetime, timezone
import enum
from sqlalchemy import Integer, String, Enum, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class OrganType(str, enum.Enum):
    kidney = "kidney"
    liver = "liver"
    heart = "heart"
    lung = "lung"
    pancreas = "pancreas"

class WaitlistStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    transplanted = "transplanted"
    deceased = "deceased"

class DonorType(str, enum.Enum):
    living = "living"
    deceased = "deceased"

class CrossmatchResult(str, enum.Enum):
    positive = "positive"
    negative = "negative"

class AcceptanceStatus(str, enum.Enum):
    offered = "offered"
    accepted = "accepted"
    declined = "declined"
    transplanted = "transplanted"

class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    organ_needed: Mapped[OrganType] = mapped_column(Enum(OrganType))
    blood_type: Mapped[str] = mapped_column(String)
    urgency_score: Mapped[int] = mapped_column(Integer)
    listed_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    transplant_center_id: Mapped[str] = mapped_column(String)
    status: Mapped[WaitlistStatus] = mapped_column(Enum(WaitlistStatus), default=WaitlistStatus.active)

class DonorOrgan(Base):
    __tablename__ = "donor_organs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    donor_id: Mapped[str] = mapped_column(String, index=True)
    donor_type: Mapped[DonorType] = mapped_column(Enum(DonorType))
    organ_type: Mapped[OrganType] = mapped_column(Enum(OrganType))
    blood_type: Mapped[str] = mapped_column(String)
    hla_typing: Mapped[Dict[str, Any]] = mapped_column(JSON)
    ischemia_time_max_hours: Mapped[float] = mapped_column(Float)
    condition_score: Mapped[int] = mapped_column(Integer)
    available_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organ_id: Mapped[int] = mapped_column(ForeignKey("donor_organs.id"))
    recipient_id: Mapped[str] = mapped_column(String)
    compatibility_score: Mapped[float] = mapped_column(Float)
    crossmatch_result: Mapped[CrossmatchResult] = mapped_column(Enum(CrossmatchResult))
    distance_km: Mapped[float] = mapped_column(Float)
    acceptance_status: Mapped[AcceptanceStatus] = mapped_column(Enum(AcceptanceStatus), default=AcceptanceStatus.offered)
    offer_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
