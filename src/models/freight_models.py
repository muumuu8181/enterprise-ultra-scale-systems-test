from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from src.database import Base

class Mode(str, enum.Enum):
    SEA = "sea"
    AIR = "air"
    RAIL = "rail"
    ROAD = "road"

class ShipmentStatus(str, enum.Enum):
    BOOKED = "booked"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    CUSTOMS = "customs"
    DELIVERED = "delivered"

class ContainerType(str, enum.Enum):
    TYPE_20FT = "20ft"
    TYPE_40FT = "40ft"
    TYPE_40HC = "40hc"
    REEFER = "reefer"

class ContainerStatus(str, enum.Enum):
    EMPTY = "empty"
    LOADED = "loaded"
    IN_TRANSIT = "in_transit"
    DISCHARGED = "discharged"

class CustomsStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CLEARED = "cleared"
    HELD = "held"

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipper_id = Column(String, index=True)
    consignee_id = Column(String, index=True)
    origin_port = Column(String)
    destination_port = Column(String)
    mode = Column(Enum(Mode))
    incoterm = Column(String)
    weight_kg = Column(Float)
    volume_cbm = Column(Float)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.BOOKED)
    etd = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)

    containers = relationship("Container", back_populates="shipment")
    customs_declaration = relationship("CustomsDeclaration", uselist=False, back_populates="shipment")

class Container(Base):
    __tablename__ = "containers"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    container_type = Column(Enum(ContainerType))
    seal_number = Column(String)
    temperature_set_c = Column(Float, nullable=True)
    weight_kg = Column(Float)
    status = Column(Enum(ContainerStatus), default=ContainerStatus.EMPTY)

    shipment = relationship("Shipment", back_populates="containers")

class CustomsDeclaration(Base):
    __tablename__ = "customs_declarations"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), unique=True)
    hs_codes = Column(JSON)
    declared_value = Column(Float)
    currency = Column(String)
    duties_amount = Column(Float)
    broker_id = Column(String)
    status = Column(Enum(CustomsStatus), default=CustomsStatus.DRAFT)

    shipment = relationship("Shipment", back_populates="customs_declaration")
