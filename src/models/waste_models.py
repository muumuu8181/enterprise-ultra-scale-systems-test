import enum
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import String, Integer, Float, DateTime, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class ContainerType(str, enum.Enum):
    drum = "drum"
    cask = "cask"
    canister = "canister"

class WasteClass(str, enum.Enum):
    LLW = "LLW"
    ILW = "ILW"
    HLW = "HLW"

class FacilityType(str, enum.Enum):
    interim = "interim"
    geological = "geological"
    pool = "pool"

class TransportStatus(str, enum.Enum):
    planned = "planned"
    in_transit = "in_transit"
    delivered = "delivered"

class StorageFacility(Base):
    __tablename__ = "storage_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    facility_type: Mapped[FacilityType] = mapped_column(SAEnum(FacilityType))
    location: Mapped[str] = mapped_column(String)
    capacity_containers: Mapped[int] = mapped_column(Integer)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    license_expiry: Mapped[datetime] = mapped_column(DateTime)
    operator_id: Mapped[str] = mapped_column(String)

    containers: Mapped[List["WasteContainer"]] = relationship("WasteContainer", back_populates="storage_location")

class WasteContainer(Base):
    __tablename__ = "waste_containers"

    id: Mapped[int] = mapped_column(primary_key=True)
    container_type: Mapped[ContainerType] = mapped_column(SAEnum(ContainerType))
    waste_class: Mapped[WasteClass] = mapped_column(SAEnum(WasteClass))
    isotopes: Mapped[Dict] = mapped_column(JSON)
    activity_becquerels: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    storage_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("storage_facilities.id"), nullable=True)
    integrity_status: Mapped[str] = mapped_column(String)
    last_inspected: Mapped[datetime] = mapped_column(DateTime)

    storage_location: Mapped[Optional["StorageFacility"]] = relationship("StorageFacility", back_populates="containers")

class TransportManifest(Base):
    __tablename__ = "transport_manifests"

    id: Mapped[int] = mapped_column(primary_key=True)
    container_ids: Mapped[List[int]] = mapped_column(JSON)
    origin_id: Mapped[int] = mapped_column(ForeignKey("storage_facilities.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("storage_facilities.id"))
    carrier: Mapped[str] = mapped_column(String)
    vehicle_id: Mapped[str] = mapped_column(String)
    route: Mapped[str] = mapped_column(String)
    departure_time: Mapped[datetime] = mapped_column(DateTime)
    arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[TransportStatus] = mapped_column(SAEnum(TransportStatus), default=TransportStatus.planned)
    regulatory_approval: Mapped[bool] = mapped_column(default=False)

    origin: Mapped["StorageFacility"] = relationship("StorageFacility", foreign_keys=[origin_id])
    destination: Mapped["StorageFacility"] = relationship("StorageFacility", foreign_keys=[destination_id])
