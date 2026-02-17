from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.core.database import Base
import enum

class EventType(str, enum.Enum):
    CONCERT = "concert"
    SPORTS = "sports"
    THEATRE = "theatre"
    FESTIVAL = "festival"

class EventStatus(str, enum.Enum):
    ON_SALE = "on_sale"
    SOLD_OUT = "sold_out"
    CANCELLED = "cancelled"

class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    capacity = Column(Integer)
    seating_map = Column(JSON)
    facilities = Column(JSON)

    events = relationship("Event", back_populates="venue")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"))
    start_time = Column(DateTime, nullable=False)
    doors_time = Column(DateTime)
    status = Column(Enum(EventStatus), default=EventStatus.ON_SALE)

    venue = relationship("Venue", back_populates="events")
    ticket_listings = relationship("TicketListing", back_populates="event")

class TicketListing(Base):
    __tablename__ = "ticket_listings"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    tier_name = Column(String, nullable=False)
    price = Column(Integer)  # Price in smallest currency unit
    quantity_total = Column(Integer)
    quantity_available = Column(Integer)
    benefits = Column(JSON)

    event = relationship("Event", back_populates="ticket_listings")
