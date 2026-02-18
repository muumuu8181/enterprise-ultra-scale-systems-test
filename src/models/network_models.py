from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

Base = declarative_base()

# Enums
class NetworkElementType(str, enum.Enum):
    enodeB = "enodeB"
    gNodeB = "gNodeB"
    MSC = "MSC"
    SGSN = "SGSN"

class OrderType(str, enum.Enum):
    new = "new"
    change = "change"
    disconnect = "disconnect"

class FaultSeverity(str, enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

class OrderStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class FaultStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    closed = "closed"

# SQLAlchemy Models

class NetworkElement(Base):
    __tablename__ = "network_elements"

    id = Column(Integer, primary_key=True, index=True)
    ne_type = Column(SQLEnum(NetworkElementType), nullable=False)
    vendor = Column(String, nullable=False)
    location = Column(String, nullable=False)
    capacity_mbps = Column(Float, nullable=False)
    current_load_pct = Column(Float, nullable=False)

    fault_tickets = relationship("FaultTicket", back_populates="network_element")


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, index=True, nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    service_id = Column(String, nullable=False)
    workflow_steps = Column(JSON, nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.pending)


class FaultTicket(Base):
    __tablename__ = "fault_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ne_id = Column(Integer, ForeignKey("network_elements.id"), nullable=False)
    fault_type = Column(String, nullable=False)
    severity = Column(SQLEnum(FaultSeverity), nullable=False)
    status = Column(SQLEnum(FaultStatus), default=FaultStatus.open)
    mttr_hours = Column(Float, nullable=True)

    network_element = relationship("NetworkElement", back_populates="fault_tickets")

# Pydantic Models for API

class NetworkElementBase(BaseModel):
    ne_type: NetworkElementType
    vendor: str
    location: str
    capacity_mbps: float
    current_load_pct: float

class NetworkElementCreate(NetworkElementBase):
    pass

class NetworkElementResponse(NetworkElementBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ServiceOrderBase(BaseModel):
    customer_id: str
    order_type: OrderType
    service_id: str
    workflow_steps: Optional[Dict[str, Any]] = None
    status: OrderStatus = OrderStatus.pending

class ServiceOrderCreate(ServiceOrderBase):
    pass

class ServiceOrderResponse(ServiceOrderBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class FaultTicketBase(BaseModel):
    ne_id: int
    fault_type: str
    severity: FaultSeverity
    status: FaultStatus = FaultStatus.open
    mttr_hours: Optional[float] = None

class FaultTicketCreate(FaultTicketBase):
    pass

class FaultTicketResponse(FaultTicketBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
