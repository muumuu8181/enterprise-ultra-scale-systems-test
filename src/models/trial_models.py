import enum
from sqlalchemy import Column, Integer, String, Date, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TrialPhase(enum.Enum):
    PHASE_I = "I"
    PHASE_II = "II"
    PHASE_III = "III"
    PHASE_IV = "IV"

class TrialStatus(enum.Enum):
    PLANNING = "planning"
    RECRUITING = "recruiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class ParticipantStatus(enum.Enum):
    SCREENING = "screening"
    ENROLLED = "enrolled"
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    COMPLETED = "completed"

class RandomizationGroup(enum.Enum):
    TREATMENT = "treatment"
    CONTROL = "control"
    PLACEBO = "placebo"

class Severity(enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class Seriousness(enum.Enum):
    SERIOUS = "serious"
    NON_SERIOUS = "non_serious"

class Causality(enum.Enum):
    RELATED = "related"
    POSSIBLY_RELATED = "possibly"
    UNRELATED = "unrelated"

class ClinicalTrial(Base):
    __tablename__ = 'clinical_trials'

    id = Column(Integer, primary_key=True, index=True)
    trial_id_nct = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    phase = Column(Enum(TrialPhase), nullable=False)
    therapeutic_area = Column(String)
    sponsor_id = Column(String)
    principal_investigator = Column(String)
    target_enrollment = Column(Integer)
    status = Column(Enum(TrialStatus), default=TrialStatus.PLANNING)
    start_date = Column(Date)

    participants = relationship("Participant", back_populates="trial")
    adverse_events = relationship("AdverseEvent", back_populates="trial")

class Participant(Base):
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey('clinical_trials.id'), nullable=False)
    subject_number = Column(String, index=True)
    demographics = Column(JSON)
    eligibility_criteria_met = Column(Boolean, default=False)
    consent_date = Column(Date)
    randomization_group = Column(Enum(RandomizationGroup), nullable=True)
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.SCREENING)

    trial = relationship("ClinicalTrial", back_populates="participants")
    adverse_events = relationship("AdverseEvent", back_populates="participant")

class AdverseEvent(Base):
    __tablename__ = 'adverse_events'

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey('participants.id'), nullable=False)
    trial_id = Column(Integer, ForeignKey('clinical_trials.id'), nullable=False)
    event_description = Column(Text, nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    seriousness = Column(Enum(Seriousness), nullable=False)
    causality = Column(Enum(Causality), nullable=False)
    onset_date = Column(Date, nullable=False)
    resolution_date = Column(Date)
    reported_to_fda = Column(Boolean, default=False)

    participant = relationship("Participant", back_populates="adverse_events")
    trial = relationship("ClinicalTrial", back_populates="adverse_events")
