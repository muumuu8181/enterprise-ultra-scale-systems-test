from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from src.database import Base

class RideType(str, enum.Enum):
    COASTER = "coaster"
    DARK_RIDE = "dark_ride"
    WATER = "water"
    SHOW = "show"
    KIDS = "kids"

class AttractionStatus(str, enum.Enum):
    OPERATING = "operating"
    TEMP_CLOSED = "temp_closed"
    MAINTENANCE = "maintenance"
    SEASONAL = "seasonal"

class TicketType(str, enum.Enum):
    SINGLE_DAY = "single_day"
    MULTI_DAY = "multi_day"
    ANNUAL = "annual"
    VIP = "vip"

class TicketStatus(str, enum.Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"

class Attraction(Base):
    __tablename__ = "attractions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    park_zone = Column(String, index=True)
    ride_type = Column(SQLEnum(RideType))
    capacity_per_hour = Column(Integer)
    height_requirement_cm = Column(Integer)
    duration_min = Column(Integer)
    status = Column(SQLEnum(AttractionStatus), default=AttractionStatus.OPERATING)

    wait_times = relationship("WaitTime", back_populates="attraction")

class WaitTime(Base):
    __tablename__ = "wait_times"

    id = Column(Integer, primary_key=True, index=True)
    attraction_id = Column(Integer, ForeignKey("attractions.id"))
    current_wait_min = Column(Integer)
    virtual_queue_enabled = Column(Boolean, default=False)
    virtual_queue_count = Column(Integer, default=0)
    fastpass_available = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    attraction = relationship("Attraction", back_populates="wait_times")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(String, index=True)
    ticket_type = Column(SQLEnum(TicketType))
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    zones_access = Column(JSON)
    fastpass_count = Column(Integer, default=0)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.ACTIVE)
