from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from src.database import Base
import enum
from datetime import datetime

class FacilityType(str, enum.Enum):
    RESTAURANT = "restaurant"
    FACTORY = "factory"
    WAREHOUSE = "warehouse"
    FARM = "farm"

class RiskCategory(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class FacilityStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class InspectionType(str, enum.Enum):
    ROUTINE = "routine"
    COMPLAINT = "complaint"
    FOLLOW_UP = "follow_up"

class InspectionResult(str, enum.Enum):
    PASS = "pass"
    CONDITIONAL = "conditional"
    FAIL = "fail"

class ViolationSeverity(str, enum.Enum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

class ViolationArea(str, enum.Enum):
    KITCHEN = "kitchen"
    STORAGE = "storage"
    HYGIENE = "hygiene"
    PEST = "pest"

class FoodFacility(Base):
    __tablename__ = "food_facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    facility_type = Column(Enum(FacilityType))
    address = Column(String)
    license_number = Column(String, unique=True, index=True)
    risk_category = Column(Enum(RiskCategory))
    last_inspection_date = Column(DateTime)
    status = Column(Enum(FacilityStatus), default=FacilityStatus.ACTIVE)

    inspections = relationship("Inspection", back_populates="facility")

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("food_facilities.id"))
    inspector_id = Column(String)
    inspection_type = Column(Enum(InspectionType))
    date = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer)
    violations = Column(JSON) # Stores summary or snapshot
    corrective_actions = Column(JSON)
    result = Column(Enum(InspectionResult))

    facility = relationship("FoodFacility", back_populates="inspections")
    violation_records = relationship("Violation", back_populates="inspection")

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    code = Column(String)
    description = Column(String)
    severity = Column(Enum(ViolationSeverity))
    area = Column(Enum(ViolationArea))
    photo_url = Column(String, nullable=True)
    corrected_on_site = Column(Boolean, default=False)

    inspection = relationship("Inspection", back_populates="violation_records")
