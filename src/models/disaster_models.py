from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.models.base import Base
import enum

class DisasterType(str, enum.Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    HURRICANE = "hurricane"
    WILDFIRE = "wildfire"
    TSUNAMI = "tsunami"

class SeverityLevel(str, enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"

class DisasterStatus(str, enum.Enum):
    ACTIVE = "active"
    RECOVERY = "recovery"
    RESOLVED = "resolved"

class OperationType(str, enum.Enum):
    SEARCH_RESCUE = "search_rescue"
    MEDICAL = "medical"
    SHELTER = "shelter"
    FOOD = "food"
    LOGISTICS = "logistics"

class OperationStatus(str, enum.Enum):
    MOBILIZING = "mobilizing"
    ACTIVE = "active"
    WINDING_DOWN = "winding_down"
    COMPLETED = "completed"

class ShipmentStatus(str, enum.Enum):
    PREPARING = "preparing"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"

class DisasterEvent(Base):
    __tablename__ = 'disaster_events'

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(SQLEnum(DisasterType), nullable=False)
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    location = Column(Geometry('GEOMETRY', srid=4326), nullable=False)
    affected_area_sq_km = Column(Float)
    affected_population = Column(Integer)
    start_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(DisasterStatus), default=DisasterStatus.ACTIVE)

    operations = relationship("ReliefOperation", back_populates="event")

class ReliefOperation(Base):
    __tablename__ = 'relief_operations'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('disaster_events.id'), nullable=False)
    operation_type = Column(SQLEnum(OperationType), nullable=False)
    lead_agency = Column(String)
    personnel_deployed = Column(Integer, default=0)
    resources = Column(JSON, default={})
    status = Column(SQLEnum(OperationStatus), default=OperationStatus.MOBILIZING)

    event = relationship("DisasterEvent", back_populates="operations")
    shipments = relationship("AidShipment", back_populates="operation")

class AidShipment(Base):
    __tablename__ = 'aid_shipments'

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey('relief_operations.id'), nullable=False)
    contents = Column(JSON, nullable=False)
    weight_kg = Column(Float)
    origin = Column(String)
    destination = Column(String)
    carrier = Column(String)
    status = Column(SQLEnum(ShipmentStatus), default=ShipmentStatus.PREPARING)
    eta = Column(DateTime(timezone=True))
    tracking_number = Column(String, unique=True, index=True)

    operation = relationship("ReliefOperation", back_populates="shipments")
