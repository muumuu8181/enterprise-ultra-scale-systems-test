from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Enum, JSON, Table
from sqlalchemy.orm import relationship
from src.database import Base
import enum

class WeddingStatus(str, enum.Enum):
    planning = "planning"
    confirmed = "confirmed"
    day_of = "day_of"
    completed = "completed"

class VendorType(str, enum.Enum):
    venue = "venue"
    catering = "catering"
    photography = "photography"
    florist = "florist"
    dj = "dj"
    cake = "cake"
    dress = "dress"

class RSVPStatus(str, enum.Enum):
    pending = "pending"
    attending = "attending"
    declined = "declined"

# Association table for many-to-many relationship between Wedding and Vendor
wedding_vendors = Table(
    'wedding_vendors', Base.metadata,
    Column('wedding_id', Integer, ForeignKey('weddings.id')),
    Column('vendor_id', Integer, ForeignKey('vendors.id'))
)

class Wedding(Base):
    __tablename__ = "weddings"

    id = Column(Integer, primary_key=True, index=True)
    couple_names = Column(String, index=True)
    wedding_date = Column(Date)
    venue_id = Column(Integer, ForeignKey("vendors.id"), nullable=True) # Assuming venue is a vendor
    guest_count = Column(Integer)
    budget = Column(Float)
    theme = Column(String)
    status = Column(Enum(WeddingStatus), default=WeddingStatus.planning)
    coordinator_id = Column(Integer, nullable=True) # Could be a User ID or similar, but User model not defined.

    guests = relationship("GuestList", back_populates="wedding")
    vendors = relationship("Vendor", secondary=wedding_vendors, backref="weddings")
    venue = relationship("Vendor", foreign_keys=[venue_id])

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    vendor_type = Column(Enum(VendorType))
    price_range = Column(String) # Could be "$", "$$", "$$$" or a numeric range
    rating = Column(Float)
    portfolio_url = Column(String)
    availability_calendar = Column(JSON)
    location = Column(String)

class GuestList(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"))
    guest_name = Column(String)
    email = Column(String)
    party_size = Column(Integer, default=1)
    rsvp_status = Column(Enum(RSVPStatus), default=RSVPStatus.pending)
    meal_preference = Column(String)
    table_number = Column(Integer, nullable=True)
    dietary_restrictions = Column(String, nullable=True)

    wedding = relationship("Wedding", back_populates="guests")
