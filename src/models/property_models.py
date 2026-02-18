from enum import Enum as PyEnum
from typing import List, Optional
from sqlalchemy import ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class PropertyType(str, PyEnum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"

class PropertyStatus(str, PyEnum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class Property(Base):
    __tablename__ = 'properties'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), nullable=False)
    units: Mapped[int] = mapped_column(default=0)
    amenities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE)

    # Relationships
    unit_list: Mapped[List["Unit"]] = relationship(back_populates="property")

class Unit(Base):
    __tablename__ = 'units'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey('properties.id'), nullable=False)
    unit_number: Mapped[str] = mapped_column(nullable=False)
    floor: Mapped[Optional[int]] = mapped_column(nullable=True)
    area_sqm: Mapped[float] = mapped_column(nullable=False)
    bedrooms: Mapped[int] = mapped_column(nullable=False)
    bathrooms: Mapped[float] = mapped_column(nullable=False)
    rent_price: Mapped[float] = mapped_column(nullable=False)
    current_tenant_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    property: Mapped["Property"] = relationship(back_populates="unit_list")
    leases: Mapped[List["Lease"]] = relationship(back_populates="unit")

class Lease(Base):
    __tablename__ = 'leases'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey('units.id'), nullable=False)
    tenant_id: Mapped[int] = mapped_column(nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    monthly_rent: Mapped[float] = mapped_column(nullable=False)
    deposit: Mapped[float] = mapped_column(nullable=False)
    terms: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    unit: Mapped["Unit"] = relationship(back_populates="leases")
