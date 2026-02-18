from datetime import datetime
from typing import Optional, Any
import enum
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class CargoType(str, enum.Enum):
    CONTAINER = "container"
    BULK = "bulk"
    LIQUID = "liquid"
    RO_RO = "ro_ro"

class DeclarationType(str, enum.Enum):
    IMPORT = "import"
    EXPORT = "export"
    TRANSIT = "transit"

class Cargo(Base):
    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(primary_key=True)
    vessel_id: Mapped[str] = mapped_column(String)
    cargo_type: Mapped[CargoType]
    weight_tonnes: Mapped[float]
    hazmat: Mapped[bool]
    container_count: Mapped[Optional[int]]
    manifest_uri: Mapped[Optional[str]] = mapped_column(String)

class PortCall(Base):
    __tablename__ = "port_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    vessel_id: Mapped[str] = mapped_column(String)
    port_id: Mapped[str] = mapped_column(String)
    berth_id: Mapped[str] = mapped_column(String)
    ata: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    atd: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cargo_loaded: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    cargo_discharged: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

class CustomsDeclaration(Base):
    __tablename__ = "customs_declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    vessel_id: Mapped[str] = mapped_column(String)
    port_id: Mapped[str] = mapped_column(String)
    declaration_type: Mapped[DeclarationType]
    status: Mapped[str] = mapped_column(String)
    inspection_required: Mapped[bool]
