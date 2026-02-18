from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class Condition(enum.Enum):
    NEW = "new"
    USED = "used"
    REFURB = "refurb"

class AuctionType(enum.Enum):
    LIVE = "live"
    TIMED = "timed"
    SEALED = "sealed"

class AuctionStatus(enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    ENDED = "ended"

class BidType(enum.Enum):
    MANUAL = "manual"
    AUTOBID = "autobid"

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    auction_type = Column(Enum(AuctionType), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.UPCOMING)

    lots = relationship("AuctionLot", back_populates="auction")

class AuctionLot(Base):
    __tablename__ = "auction_lots"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"))
    seller_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    category = Column(String)
    description = Column(String)
    images = Column(JSON)
    condition = Column(Enum(Condition), nullable=False)
    reserve_price = Column(Float)
    estimate_low = Column(Float)
    estimate_high = Column(Float)

    auction = relationship("Auction", back_populates="lots")
    bids = relationship("Bid", back_populates="lot")

class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("auction_lots.id"), nullable=False)
    bidder_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    is_winning = Column(Boolean, default=False)
    bid_type = Column(Enum(BidType), nullable=False)

    lot = relationship("AuctionLot", back_populates="bids")
