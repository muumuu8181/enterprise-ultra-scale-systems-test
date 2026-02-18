from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List, Optional
from src.models.clinical_models import TrialPhase, TrialStatus, TreatmentArm, Severity

class ClinicalTrialCreate(BaseModel):
    compound_id: str
    phase: TrialPhase
    enrollment_target: int
    primary_endpoint: str
    start_date: date

class ClinicalTrialRead(ClinicalTrialCreate):
    id: int
    status: TrialStatus
    model_config = ConfigDict(from_attributes=True)

class TrialSubjectEnroll(BaseModel):
    subject_code: str
    age: int
    sex: str
    baseline_score: float
    treatment_arm: TreatmentArm

class TrialSubjectRead(TrialSubjectEnroll):
    id: int
    trial_id: int
    model_config = ConfigDict(from_attributes=True)

class AdverseEventReport(BaseModel):
    subject_id: int
    event_type: str
    severity: Severity
    causality: str

class AdverseEventRead(AdverseEventReport):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SurvivalResult(BaseModel):
    trial_id: int
    median_survival: float
    hazard_ratio: float
    p_value: float

class ClinicalReport(BaseModel):
    trial_id: int
    total_subjects: int
    active_subjects: int
    dropped_out_subjects: int
    adverse_events_count: int
    report_date: date

class StatisticalAnalysisRequest(BaseModel):
    effect_size: float
    power: float
    alpha: float

class StatisticalAnalysisResult(BaseModel):
    required_sample_size: int
