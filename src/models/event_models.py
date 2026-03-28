import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class EventType(str, enum.Enum):
    CONFERENCE = "conference"
    CONCERT = "concert"
    WORKSHOP = "workshop"
    WEBINAR = "webinar"

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organizer_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType))
    venue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("venues.id"), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    ticket_types: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})
    status: Mapped[EventStatus] = mapped_column(SQLEnum(EventStatus), default=EventStatus.DRAFT)

    registrations: Mapped[List["Registration"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    venue: Mapped[Optional["Venue"]] = relationship(back_populates="events")

class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    attendee_id: Mapped[int] = mapped_column(Integer, index=True)
    ticket_type: Mapped[str] = mapped_column(String)
    amount_paid: Mapped[float] = mapped_column(Float)
    registration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    badge_printed: Mapped[bool] = mapped_column(default=False)
    dietary_preference: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    event: Mapped["Event"] = relationship(back_populates="registrations")

class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    address: Mapped[str] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer)
    facilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})
    hourly_rate: Mapped[float] = mapped_column(Float)
    availability_calendar: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})
    contact_email: Mapped[str] = mapped_column(String)

    events: Mapped[List["Event"]] = relationship(back_populates="venue")
