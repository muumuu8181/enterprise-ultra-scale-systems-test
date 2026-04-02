import enum
from sqlalchemy import Column, Integer, String, Float, Enum, JSON, Date, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.core.database import Base

class Element(str, enum.Enum):
    NEODYMIUM = "neodymium"
    DYSPROSIUM = "dysprosium"
    LANTHANUM = "lanthanum"
    CERIUM = "cerium"

class MiningStatus(str, enum.Enum):
    EXPLORATION = "exploration"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    CLOSED = "closed"

class ContractStatus(str, enum.Enum):
    NEGOTIATING = "negotiating"
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    TERMINATED = "terminated"

class MineralDeposit(Base):
    __tablename__ = "mineral_deposits"

    id = Column(Integer, primary_key=True, index=True)
    element = Column(Enum(Element), nullable=False)
    location = Column(Geometry("POINT"), nullable=False)  # Assuming Point for simplicity, could be Polygon
    estimated_reserves_tonnes = Column(Float, nullable=False)
    grade_pct = Column(Float, nullable=False)
    mining_status = Column(Enum(MiningStatus), default=MiningStatus.EXPLORATION)
    operator_id = Column(String, nullable=False)

    batches = relationship("ProcessingBatch", back_populates="deposit")

class SupplyContract(Base):
    __tablename__ = "supply_contracts"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String, nullable=False)
    seller_id = Column(String, nullable=False)
    element = Column(Enum(Element), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    delivery_schedule = Column(JSON, nullable=True)
    incoterm = Column(String, nullable=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.NEGOTIATING)

class ProcessingBatch(Base):
    __tablename__ = "processing_batches"

    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(Integer, ForeignKey("mineral_deposits.id"), nullable=False)
    input_ore_tonnes = Column(Float, nullable=False)
    output_elements = Column(JSON, nullable=False)  # e.g., {"neodymium": 10.5, "dysprosium": 2.1}
    recovery_rate_pct = Column(Float, nullable=False)
    environmental_compliance = Column(String, nullable=True) # Could be JSON or Enum, sticking to String/JSON as per prompt hint "environmental_compliance"
    batch_date = Column(Date, nullable=False)
    quality_cert_url = Column(String, nullable=True)

    deposit = relationship("MineralDeposit", back_populates="batches")
