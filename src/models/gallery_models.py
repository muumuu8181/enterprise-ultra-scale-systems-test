import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.database import Base

class ArtworkLocation(str, enum.Enum):
    GALLERY = "gallery"
    STORAGE = "storage"
    LOAN = "loan"
    SOLD = "sold"

class ExhibitionStatus(str, enum.Enum):
    PLANNING = "planning"
    CURRENT = "current"
    PAST = "past"

class SaleType(str, enum.Enum):
    GALLERY = "gallery"
    AUCTION = "auction"
    PRIVATE = "private"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"

class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist_id = Column(Integer, nullable=False, index=True) # Assuming artist is in another system or simplified
    medium = Column(String)
    dimensions = Column(String)
    year_created = Column(Integer)
    edition = Column(String)
    price = Column(Float)
    reserve_price = Column(Float)
    location = Column(Enum(ArtworkLocation), default=ArtworkLocation.STORAGE)
    condition = Column(String)
    provenance = Column(JSON) # List of previous owners/history

    sales = relationship("Sale", back_populates="artwork")

class Exhibition(Base):
    __tablename__ = "exhibitions"

    id = Column(Integer, primary_key=True, index=True)
    gallery_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    curator = Column(String)
    theme = Column(String)
    opening_date = Column(DateTime)
    closing_date = Column(DateTime)
    artworks = Column(JSON) # List of artwork IDs included
    catalog_url = Column(String)
    status = Column(Enum(ExhibitionStatus), default=ExhibitionStatus.PLANNING)

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    buyer_id = Column(Integer, nullable=False)
    sale_type = Column(Enum(SaleType), nullable=False)
    hammer_price = Column(Float)
    commission_pct = Column(Float)
    total_amount = Column(Float)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    sold_at = Column(DateTime, default=datetime.utcnow)

    artwork = relationship("Artwork", back_populates="sales")
