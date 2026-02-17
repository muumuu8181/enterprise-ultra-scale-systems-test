from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    JSON,
    ForeignKey,
    DateTime,
    Enum,
    Float,
)
from sqlalchemy.orm import declarative_base, relationship
import enum
import datetime

Base = declarative_base()

class TreatmentStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class AppointmentType(str, enum.Enum):
    CLEANING = "cleaning"
    FILLING = "filling"
    CROWN = "crown"
    ROOT_CANAL = "root_canal"
    EXTRACTION = "extraction"
    IMPLANT = "implant"
    ORTHODONTIC = "orthodontic"

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_CHAIR = "in_chair"
    COMPLETED = "completed"

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    insurance_id = Column(String, nullable=True)
    allergies = Column(JSON, default=list)
    medical_conditions = Column(JSON, default=list)
    last_xray_date = Column(Date, nullable=True)
    next_cleaning_due = Column(Date, nullable=True)
    balance_due = Column(Float, default=0.0)

    treatment_plans = relationship("TreatmentPlan", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")

class TreatmentPlan(Base):
    __tablename__ = "treatment_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    dentist_id = Column(Integer, nullable=False)
    procedures = Column(JSON, default=list)
    total_cost = Column(Float, nullable=False)
    insurance_coverage = Column(Float, nullable=False)
    patient_responsibility = Column(Float, nullable=False)
    status = Column(Enum(TreatmentStatus), default=TreatmentStatus.PROPOSED)
    valid_until = Column(Date, nullable=True)

    patient = relationship("Patient", back_populates="treatment_plans")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    dentist_id = Column(Integer, nullable=True)
    hygienist_id = Column(Integer, nullable=True)
    appointment_type = Column(Enum(AppointmentType), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    chair_number = Column(Integer, nullable=False)
    duration_min = Column(Integer, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)

    patient = relationship("Patient", back_populates="appointments")
