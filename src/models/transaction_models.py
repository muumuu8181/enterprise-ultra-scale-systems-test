from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from src.database import Base

class PropertyType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"

class PropertyStatus(str, enum.Enum):
    LISTED = "listed"
    PENDING = "pending"
    SOLD = "sold"

class OfferStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class EscrowStatus(str, enum.Enum):
    PENDING = "pending"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String, index=True)
    property_type: Mapped[PropertyType] = mapped_column(SAEnum(PropertyType))
    bedrooms: Mapped[int] = mapped_column(Integer)
    area_sqm: Mapped[float] = mapped_column(Float)
    year_built: Mapped[int] = mapped_column(Integer)
    list_price: Mapped[float] = mapped_column(Float)
    status: Mapped[PropertyStatus] = mapped_column(SAEnum(PropertyStatus), default=PropertyStatus.LISTED)

    offers = relationship("Offer", back_populates="property", cascade="all, delete-orphan")
    escrows = relationship("Escrow", back_populates="property", cascade="all, delete-orphan")

class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    buyer_id: Mapped[str] = mapped_column(String)
    offer_price: Mapped[float] = mapped_column(Float)
    contingencies: Mapped[dict] = mapped_column(JSON)
    expiry_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[OfferStatus] = mapped_column(SAEnum(OfferStatus), default=OfferStatus.PENDING)

    property = relationship("Property", back_populates="offers")

class Escrow(Base):
    __tablename__ = "escrows"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    buyer_id: Mapped[str] = mapped_column(String)
    seller_id: Mapped[str] = mapped_column(String)
    escrow_amount: Mapped[float] = mapped_column(Float)
    closing_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[EscrowStatus] = mapped_column(SAEnum(EscrowStatus), default=EscrowStatus.PENDING)

    property = relationship("Property", back_populates="escrows")
