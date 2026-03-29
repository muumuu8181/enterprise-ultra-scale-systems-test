from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from geoalchemy2 import Geometry
from enum import Enum
from datetime import datetime
from src.database import Base

class IncidentType(str, Enum):
    FIRE = "fire"
    EMS = "ems"
    HAZMAT = "hazmat"
    RESCUE = "rescue"
    FALSE_ALARM = "false_alarm"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(str, Enum):
    REPORTED = "reported"
    DISPATCHED = "dispatched"
    ON_SCENE = "on_scene"
    RESOLVED = "resolved"

class FireStationStatus(str, Enum):
    AVAILABLE = "available"
    PARTIALLY_AVAILABLE = "partially_available"
    UNAVAILABLE = "unavailable"

class ApparatusType(str, Enum):
    ENGINE = "engine"
    LADDER = "ladder"
    RESCUE = "rescue"
    AMBULANCE = "ambulance"
    HAZMAT = "hazmat"

class ApparatusStatus(str, Enum):
    IN_SERVICE = "in_service"
    ON_CALL = "on_call"
    OUT_OF_SERVICE = "out_of_service"

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_type: Mapped[IncidentType] = mapped_column(SAEnum(IncidentType))
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority))
    location = Column(Geometry('POINT'))
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(SAEnum(IncidentStatus), default=IncidentStatus.REPORTED)

class FireStation(Base):
    __tablename__ = "fire_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    location = Column(Geometry('POINT'))
    district: Mapped[str] = mapped_column(String, index=True)
    units: Mapped[dict] = mapped_column(JSON)
    personnel_on_duty: Mapped[int] = mapped_column(Integer)
    status: Mapped[FireStationStatus] = mapped_column(SAEnum(FireStationStatus))

    apparatus: Mapped[list["Apparatus"]] = relationship("Apparatus", back_populates="station")

class Apparatus(Base):
    __tablename__ = "apparatus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("fire_stations.id"))
    unit_type: Mapped[ApparatusType] = mapped_column(SAEnum(ApparatusType))
    call_sign: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[ApparatusStatus] = mapped_column(SAEnum(ApparatusStatus))
    mileage: Mapped[float] = mapped_column(Float)
    last_maintenance: Mapped[datetime] = mapped_column(DateTime)

    station: Mapped["FireStation"] = relationship("FireStation", back_populates="apparatus")
