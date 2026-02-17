from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum
from datetime import datetime, timezone
from src.database import Base
import enum

class EscrowStatus(str, enum.Enum):
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"

class BuyersPremium(Base):
    __tablename__ = "buyers_premiums"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(String, index=True)
    tier_structure = Column(JSON)

class EscrowAccount(Base):
    __tablename__ = "escrow_accounts"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(String, index=True)
    buyer_id = Column(String, index=True)
    amount = Column(Float)
    status = Column(Enum(EscrowStatus), default=EscrowStatus.HELD)

class AuctionSettlement(Base):
    __tablename__ = "auction_settlements"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(String, unique=True, index=True)
    hammer_price = Column(Float)
    buyers_premium = Column(Float)
    seller_proceeds = Column(Float)
    platform_commission = Column(Float)
    settled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
