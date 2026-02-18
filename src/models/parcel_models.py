from enum import Enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

class ServiceType(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"

class EventType(str, Enum):
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"

class CarrierName(str, Enum):
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"
    USPS = "usps"

class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(primary_key=True)
    tracking_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    sender_id: Mapped[int] = mapped_column(Integer)
    recipient_address: Mapped[dict] = mapped_column(JSON)
    weight_kg: Mapped[float] = mapped_column(Float)
    dimensions: Mapped[dict] = mapped_column(JSON)
    service_type: Mapped[ServiceType] = mapped_column(String)

    events: Mapped[List["ShipmentEvent"]] = relationship(back_populates="parcel")

class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"))
    event_type: Mapped[EventType] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="events")

class CarrierIntegration(Base):
    __tablename__ = "carrier_integrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrier_name: Mapped[CarrierName] = mapped_column(String, unique=True)
    api_credentials: Mapped[dict] = mapped_column(JSON)
    supported_services: Mapped[List[str]] = mapped_column(JSON)
