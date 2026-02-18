from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.db.base import Base

class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    sku: Mapped[str] = mapped_column(String, unique=True, index=True)
    unit: Mapped[str] = mapped_column(String)
    stock_qty: Mapped[float] = mapped_column(Float, default=0.0)
    reorder_point: Mapped[float] = mapped_column(Float, default=0.0)
    lead_days: Mapped[int] = mapped_column(Integer, default=0)

class BillOfMaterials(Base):
    __tablename__ = "bill_of_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)  # Assuming external Product ID
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_materials.id"))
    qty_required: Mapped[float] = mapped_column(Float)
    waste_factor: Mapped[float] = mapped_column(Float, default=0.0)

    material: Mapped["RawMaterial"] = relationship("RawMaterial")

class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    bom_id: Mapped[int] = mapped_column(Integer, ForeignKey("bill_of_materials.id"))  # Optional: link to BOM used
    planned_qty: Mapped[float] = mapped_column(Float)
    material_reservations: Mapped[dict] = mapped_column(JSON, default={})
    status: Mapped[str] = mapped_column(String, default="PLANNED") # Added status for "issue-materials" logic

    bom: Mapped["BillOfMaterials"] = relationship("BillOfMaterials")
