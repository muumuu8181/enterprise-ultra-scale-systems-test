from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime

Base = declarative_base()

class StadiumStatus(str, enum.Enum):
    OPEN = "open"
    EVENT = "event"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"

class EventType(str, enum.Enum):
    FOOTBALL = "football"
    CONCERT = "concert"
    CONFERENCE = "conference"
    BOXING = "boxing"

class EventStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    GATES_OPEN = "gates_open"
    LIVE = "live"
    COMPLETED = "completed"

class ConcessionStandType(str, enum.Enum):
    FOOD = "food"
    BEVERAGE = "beverage"
    MERCHANDISE = "merchandise"

class ConcessionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

class Stadium(Base):
    __tablename__ = 'stadiums'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    sections = Column(JSON, nullable=True)
    facilities = Column(JSON, nullable=True)
    owner_id = Column(Integer, nullable=False)
    status = Column(SAEnum(StadiumStatus), default=StadiumStatus.OPEN)

    events = relationship("Event", back_populates="stadium")
    concessions = relationship("Concession", back_populates="stadium")

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    stadium_id = Column(Integer, ForeignKey('stadiums.id'), nullable=False)
    event_type = Column(SAEnum(EventType), nullable=False)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    kickoff_time = Column(DateTime, nullable=False)
    expected_attendance = Column(Integer, nullable=True)
    ticket_tiers = Column(JSON, nullable=True)
    status = Column(SAEnum(EventStatus), default=EventStatus.SCHEDULED)

    stadium = relationship("Stadium", back_populates="events")

class Concession(Base):
    __tablename__ = 'concessions'

    id = Column(Integer, primary_key=True, index=True)
    stadium_id = Column(Integer, ForeignKey('stadiums.id'), nullable=False)
    section = Column(String, nullable=False)
    stand_type = Column(SAEnum(ConcessionStandType), nullable=False)
    items = Column(JSON, nullable=True)
    revenue_today = Column(Integer, default=0)
    inventory_alerts = Column(JSON, nullable=True)
    status = Column(SAEnum(ConcessionStatus), default=ConcessionStatus.CLOSED)

    stadium = relationship("Stadium", back_populates="concessions")
