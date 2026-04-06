from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import List, Optional

class Base(DeclarativeBase):
    pass

class WaferSize(int, enum.Enum):
    SIZE_200 = 200
    SIZE_300 = 300

class LotStatus(str, enum.Enum):
    IN_PROCESS = "in_process"
    HOLD = "hold"
    COMPLETED = "completed"
    SCRAPPED = "scrapped"

class EquipmentType(str, enum.Enum):
    LITHOGRAPHY = "lithography"
    ETCH = "etch"
    DEPOSITION = "deposition"
    IMPLANT = "implant"
    METROLOGY = "metrology"

class EquipmentStatus(str, enum.Enum):
    RUNNING = "running"
    IDLE = "idle"
    PM = "pm"
    DOWN = "down"

class WaferLot(Base):
    __tablename__ = 'wafer_lots'

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    wafer_size_mm: Mapped[WaferSize] = mapped_column(SAEnum(WaferSize))
    process_node_nm: Mapped[int] = mapped_column(Integer)
    product: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    current_step: Mapped[str] = mapped_column(String)
    yield_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[LotStatus] = mapped_column(SAEnum(LotStatus), default=LotStatus.IN_PROCESS)

    steps: Mapped[List["ProcessStep"]] = relationship(back_populates="lot")

class Equipment(Base):
    __tablename__ = 'equipment'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    equipment_type: Mapped[EquipmentType] = mapped_column(SAEnum(EquipmentType))
    chamber_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[EquipmentStatus] = mapped_column(SAEnum(EquipmentStatus))
    pm_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    utilization_pct: Mapped[float] = mapped_column(Float, default=0.0)

    steps: Mapped[List["ProcessStep"]] = relationship(back_populates="equipment")

class ProcessStep(Base):
    __tablename__ = 'process_steps'

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey('wafer_lots.id'))
    step_name: Mapped[str] = mapped_column(String)
    equipment_id: Mapped[int] = mapped_column(ForeignKey('equipment.id'))
    recipe: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    measurements: Mapped[dict] = mapped_column(JSON)
    pass_fail: Mapped[bool] = mapped_column(Boolean)
    operator_id: Mapped[str] = mapped_column(String)

    lot: Mapped["WaferLot"] = relationship(back_populates="steps")
    equipment: Mapped["Equipment"] = relationship(back_populates="steps")
