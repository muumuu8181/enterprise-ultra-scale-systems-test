from enum import Enum, IntEnum
from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.db.base import Base

class TrialPhase(IntEnum):
    PHASE_1 = 1
    PHASE_2 = 2
    PHASE_3 = 3
    PHASE_4 = 4

class TrialStatus(str, Enum):
    PLANNED = "planned"
    RECRUITING = "recruiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class TreatmentArm(str, Enum):
    DRUG = "drug"
    PLACEBO = "placebo"

class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"

class ClinicalTrial(Base):
    __tablename__ = "clinical_trials"

    id = Column(Integer, primary_key=True, index=True)
    compound_id = Column(String, index=True)
    phase = Column(SQLEnum(TrialPhase))
    status = Column(SQLEnum(TrialStatus), default=TrialStatus.PLANNED)
    enrollment_target = Column(Integer)
    primary_endpoint = Column(String)
    start_date = Column(Date)

    subjects = relationship("TrialSubject", back_populates="trial")

class TrialSubject(Base):
    __tablename__ = "trial_subjects"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("clinical_trials.id"))
    subject_code = Column(String, unique=True, index=True)
    age = Column(Integer)
    sex = Column(String)
    baseline_score = Column(Float)
    treatment_arm = Column(SQLEnum(TreatmentArm))

    trial = relationship("ClinicalTrial", back_populates="subjects")
    adverse_events = relationship("AdverseEvent", back_populates="subject")

class AdverseEvent(Base):
    __tablename__ = "adverse_events"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("trial_subjects.id"))
    event_type = Column(String)
    severity = Column(SQLEnum(Severity))
    causality = Column(String)

    subject = relationship("TrialSubject", back_populates="adverse_events")
