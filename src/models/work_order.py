from sqlalchemy import String, Integer, Float, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base
import enum

class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    PREDICTIVE = "predictive"
    CORRECTIVE = "corrective"

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    equipment_id: Mapped[str] = mapped_column(String, index=True)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(Enum(MaintenanceType))
    priority: Mapped[int] = mapped_column(Integer)
    assigned_technician: Mapped[str] = mapped_column(String, nullable=True)
    estimated_hours: Mapped[float] = mapped_column(Float)
    parts_needed: Mapped[dict] = mapped_column(JSON)
    cost_estimate: Mapped[float] = mapped_column(Float)

class TechnicianSkill(Base):
    __tablename__ = "technician_skills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    technician_id: Mapped[str] = mapped_column(String, index=True)
    skill_type: Mapped[str] = mapped_column(String)
    certification_level: Mapped[str] = mapped_column(String)
    equipment_types: Mapped[list] = mapped_column(JSON)

class SparePart(Base):
    __tablename__ = "spare_parts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    part_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    compatible_equipment: Mapped[list] = mapped_column(JSON)
    stock_qty: Mapped[int] = mapped_column(Integer)
    lead_days: Mapped[int] = mapped_column(Integer)
    unit_cost: Mapped[float] = mapped_column(Float)
