from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
import enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class Base(DeclarativeBase):
    pass

class RobotType(str, enum.Enum):
    PICKER = "picker"
    CARRIER = "carrier"
    SORTER = "sorter"

class RobotStatus(str, enum.Enum):
    IDLE = "idle"
    WORKING = "working"
    CHARGING = "charging"
    ERROR = "error"

class TaskType(str, enum.Enum):
    PICK = "pick"
    CARRY = "carry"
    SORT = "sort"
    CHARGE = "charge"

class ZoneType(str, enum.Enum):
    STORAGE = "storage"
    PICKING = "picking"
    SHIPPING = "shipping"
    CHARGING = "charging"

# SQLAlchemy Models

class WarehouseZone(Base):
    __tablename__ = "warehouse_zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    zone_type: Mapped[ZoneType] = mapped_column(Enum(ZoneType))
    capacity: Mapped[int] = mapped_column(Integer)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)

    robots: Mapped[list["Robot"]] = relationship("Robot", back_populates="zone")

class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    serial: Mapped[str] = mapped_column(String, unique=True, index=True)
    robot_type: Mapped[RobotType] = mapped_column(Enum(RobotType))
    status: Mapped[RobotStatus] = mapped_column(Enum(RobotStatus), default=RobotStatus.IDLE)
    battery_pct: Mapped[float] = mapped_column(Float)
    current_task_id: Mapped[int | None] = mapped_column(ForeignKey("robot_tasks.id", use_alter=True, name="fk_robot_current_task"), nullable=True)
    location_zone_id: Mapped[int | None] = mapped_column(ForeignKey("warehouse_zones.id"), nullable=True)

    zone: Mapped["WarehouseZone"] = relationship("WarehouseZone", back_populates="robots")
    # Use string for class name to resolve forward reference, and specify foreign_keys
    current_task = relationship("RobotTask", foreign_keys=[current_task_id], post_update=True)
    tasks: Mapped[list["RobotTask"]] = relationship("RobotTask", back_populates="robot", foreign_keys="RobotTask.robot_id")

class RobotTask(Base):
    __tablename__ = "robot_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    robot_id: Mapped[int | None] = mapped_column(ForeignKey("robots.id"), nullable=True)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    robot: Mapped["Robot"] = relationship("Robot", back_populates="tasks", foreign_keys=[robot_id])

# Pydantic Schemas

class RobotBase(BaseModel):
    serial: str
    robot_type: RobotType
    status: RobotStatus
    battery_pct: float
    location_zone_id: Optional[int] = None

class RobotCreate(RobotBase):
    pass

class RobotRead(RobotBase):
    id: int
    current_task_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    task_type: TaskType
    priority: int
    payload: Dict[str, Any]

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    id: int
    robot_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ZoneBase(BaseModel):
    name: str
    zone_type: ZoneType
    capacity: int

class ZoneRead(ZoneBase):
    id: int
    current_occupancy: int
    model_config = ConfigDict(from_attributes=True)

class Assignment(BaseModel):
    robot_id: int
    task_id: int
