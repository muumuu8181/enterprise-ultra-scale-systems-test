from typing import Optional, List
from datetime import datetime, timezone
import enum

from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, Text, Enum as SQLEnum, Numeric, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from src.core.database import Base

# Helper for BigInteger primary keys compatible with SQLite autoincrement
def BigIntPK():
    return BigInteger().with_variant(Integer, "sqlite")

class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"

class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    TOUR_3D = "3d-tour"

class ListingType(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"

class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    RENTED = "rented"
    EXPIRED = "expired"

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(BigIntPK(), primary_key=True)
    type: Mapped[PropertyType] = mapped_column(SQLEnum(PropertyType), nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    # Using management=True for SQLite compatibility (requires spatialite usually)
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    media: Mapped[List["PropertyMedia"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    listings: Mapped[List["Listing"]] = relationship(back_populates="property", cascade="all, delete-orphan")

class PropertyMedia(Base):
    __tablename__ = "property_media"

    id: Mapped[int] = mapped_column(BigIntPK(), primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(SQLEnum(MediaType), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    property: Mapped["Property"] = relationship(back_populates="media")

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(BigIntPK(), primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    agent_id: Mapped[int] = mapped_column(Integer, nullable=False)
    listing_type: Mapped[ListingType] = mapped_column(SQLEnum(ListingType), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[ListingStatus] = mapped_column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE)
    listed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    property: Mapped["Property"] = relationship(back_populates="listings")
    inquiries: Mapped[List["PropertyInquiry"]] = relationship(back_populates="listing", cascade="all, delete-orphan")

class PropertyInquiry(Base):
    __tablename__ = "property_inquiries"

    id: Mapped[int] = mapped_column(BigIntPK(), primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_visit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")

    listing: Mapped["Listing"] = relationship(back_populates="inquiries")
