from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.database import Base
import enum
from datetime import datetime

class ChannelType(str, enum.Enum):
    TV = "tv"
    RADIO = "radio"
    STREAMING = "streaming"

class ChannelStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFF_AIR = "off_air"

class ProgramRating(str, enum.Enum):
    G = "G"
    PG = "PG"
    PG13 = "PG13"
    R = "R"

class ProgramStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    AIRED = "aired"
    CANCELLED = "cancelled"

class AdSlotPosition(str, enum.Enum):
    PRE = "pre"
    MID = "mid"
    POST = "post"

class AdSlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    AIRED = "aired"

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    channel_type = Column(Enum(ChannelType), nullable=False)
    frequency = Column(String, nullable=True)
    region = Column(String, nullable=True)
    owner_id = Column(Integer, nullable=True)
    status = Column(Enum(ChannelStatus), default=ChannelStatus.ACTIVE, nullable=False)

    programs = relationship("Program", back_populates="channel")

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    genre = Column(String, nullable=True)
    duration_min = Column(Integer, nullable=False)
    rating = Column(Enum(ProgramRating), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(Enum(ProgramStatus), default=ProgramStatus.SCHEDULED, nullable=False)

    channel = relationship("Channel", back_populates="programs")
    ad_slots = relationship("AdSlot", back_populates="program")

class AdSlot(Base):
    __tablename__ = "ad_slots"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    position = Column(Enum(AdSlotPosition), nullable=False)
    duration_sec = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    advertiser_id = Column(Integer, nullable=True)
    creative_url = Column(String, nullable=True)
    impressions = Column(Integer, default=0)
    status = Column(Enum(AdSlotStatus), default=AdSlotStatus.AVAILABLE, nullable=False)

    program = relationship("Program", back_populates="ad_slots")
