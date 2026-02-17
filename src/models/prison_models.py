from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone
from src.database import Base

class SecurityLevel(str, enum.Enum):
    MINIMUM = "minimum"
    MEDIUM = "medium"
    MAXIMUM = "maximum"
    SUPERMAX = "supermax"

class InmateStatus(str, enum.Enum):
    INCARCERATED = "incarcerated"
    TRANSFERRED = "transferred"
    RELEASED = "released"
    PAROLE = "parole"

class CellStatus(str, enum.Enum):
    OCCUPIED = "occupied"
    VACANT = "vacant"
    MAINTENANCE = "maintenance"

class IncidentType(str, enum.Enum):
    ASSAULT = "assault"
    CONTRABAND = "contraband"
    ESCAPE_ATTEMPT = "escape_attempt"
    MEDICAL = "medical"
    FIRE = "fire"

class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"

class Cell(Base):
    __tablename__ = "cells"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(String, index=True)
    cell_number = Column(String, unique=True, index=True)
    capacity = Column(Integer, default=1)
    current_occupancy = Column(Integer, default=0)
    security_level = Column(SQLEnum(SecurityLevel))
    status = Column(SQLEnum(CellStatus), default=CellStatus.VACANT)
    last_inspection = Column(DateTime(timezone=True))

    inmates = relationship("Inmate", back_populates="cell")

class Inmate(Base):
    __tablename__ = "inmates"

    id = Column(Integer, primary_key=True, index=True)
    inmate_number = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    dob = Column(Date)
    sentence_start = Column(Date)
    sentence_end = Column(Date, nullable=True)
    offense_category = Column(String)
    security_level = Column(SQLEnum(SecurityLevel))
    cell_id = Column(Integer, ForeignKey("cells.id"), nullable=True)
    status = Column(SQLEnum(InmateStatus), default=InmateStatus.INCARCERATED)

    cell = relationship("Cell", back_populates="inmates")
    incidents = relationship("Incident", back_populates="inmate")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    inmate_id = Column(Integer, ForeignKey("inmates.id"))
    incident_type = Column(SQLEnum(IncidentType))
    severity = Column(String)
    location = Column(String)
    reported_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    investigating_officer = Column(String)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.REPORTED)

    inmate = relationship("Inmate", back_populates="incidents")
