from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime

Base = declarative_base()

class GeneratorType(str, enum.Enum):
    solar = "solar"
    wind = "wind"
    hydro = "hydro"
    nuclear = "nuclear"

class BidStatus(str, enum.Enum):
    pending = "pending"
    matched = "matched"
    expired = "expired"

class TradeType(str, enum.Enum):
    spot = "spot"
    forward = "forward"

class EnergyGenerator(Base):
    __tablename__ = "energy_generators"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, index=True)
    generator_type = Column(Enum(GeneratorType))
    capacity_mw = Column(Float)
    location = Column(JSON)  # GeoJSON
    feed_in_tariff = Column(Float)
    grid_connected = Column(Boolean)

class EnergyBid(Base):
    __tablename__ = "energy_bids"

    id = Column(Integer, primary_key=True, index=True)
    generator_id = Column(Integer, ForeignKey("energy_generators.id"))
    volume_mwh = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    delivery_period = Column(String)  # Representation of period
    status = Column(Enum(BidStatus), default=BidStatus.pending)

class EnergyTrade(Base):
    __tablename__ = "energy_trades"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String)
    seller_id = Column(String)
    volume_mwh = Column(Float)
    price_per_mwh = Column(Float)
    delivery_start = Column(DateTime)
    delivery_end = Column(DateTime)
    trade_type = Column(Enum(TradeType))
