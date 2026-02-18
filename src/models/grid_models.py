from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from src.database import Base

class NodeStatus(enum.Enum):
    NORMAL = "normal"
    OVERLOADED = "overloaded"
    FAULT = "fault"

class LineStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class GridNode(Base):
    __tablename__ = "grid_nodes"

    id = Column(Integer, primary_key=True)
    node_id = Column(String, unique=True, nullable=False)
    voltage_kv = Column(Float, nullable=False)
    frequency_hz = Column(Float, nullable=False)
    load_mw = Column(Float, nullable=False)
    generation_mw = Column(Float, nullable=False)
    status = Column(Enum(NodeStatus), nullable=False)

class TransmissionLine(Base):
    __tablename__ = "transmission_lines"

    id = Column(Integer, primary_key=True)
    from_node = Column(Integer, ForeignKey("grid_nodes.id"), nullable=False)
    to_node = Column(Integer, ForeignKey("grid_nodes.id"), nullable=False)
    capacity_mw = Column(Float, nullable=False)
    current_load_mw = Column(Float, nullable=False)
    resistance_ohm = Column(Float, nullable=False)
    status = Column(Enum(LineStatus), nullable=False)

    source_node_rel = relationship("GridNode", foreign_keys=[from_node])
    target_node_rel = relationship("GridNode", foreign_keys=[to_node])

class CongestionEvent(Base):
    __tablename__ = "congestion_events"

    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey("transmission_lines.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    severity = Column(String, nullable=False)
    redispatch_cost = Column(Float, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    line = relationship("TransmissionLine")
