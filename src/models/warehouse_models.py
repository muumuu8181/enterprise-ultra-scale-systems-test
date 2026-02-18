from sqlalchemy import Column, Integer, String, Float, JSON, Enum
from src.database import Base
import enum

class StorageLocation(Base):
    __tablename__ = "storage_locations"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, index=True)
    aisle = Column(String)
    rack = Column(String)
    level = Column(String)
    bin = Column(String)
    sku = Column(String, index=True)
    quantity = Column(Integer, default=0)
    reserved_qty = Column(Integer, default=0)

class PickListStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PickList(Base):
    __tablename__ = "pick_lists"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    items = Column(JSON)
    assigned_robot_id = Column(String, nullable=True)
    status = Column(Enum(PickListStatus), default=PickListStatus.PENDING)
    completion_pct = Column(Float, default=0.0)

class TriggerType(str, enum.Enum):
    MIN_STOCK = "min_stock"
    FORECAST = "forecast"

class ReplenishmentOrder(Base):
    __tablename__ = "replenishment_orders"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True)
    from_zone = Column(String)
    to_zone = Column(String)
    quantity = Column(Integer)
    triggered_by = Column(Enum(TriggerType))
