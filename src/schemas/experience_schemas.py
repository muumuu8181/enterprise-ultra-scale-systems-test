from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    OFFBOARDED = "offboarded"

class SurveyType(str, Enum):
    PULSE = "pulse"
    QUARTERLY = "quarterly"
    EXIT = "exit"

class MetricType(str, Enum):
    STRESS = "stress"
    SATISFACTION = "satisfaction"
    BELONGING = "belonging"
    GROWTH = "growth"

class EmployeeBase(BaseModel):
    employee_number: str
    name: str
    department: str
    role: str
    manager_id: Optional[int] = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    engagement_score: float = 0.0

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id: int
    hire_date: datetime

    model_config = ConfigDict(from_attributes=True)

class SurveyResponseBase(BaseModel):
    employee_id: Optional[int] = None
    survey_type: SurveyType
    responses: Dict[str, Any]
    sentiment_score: float
    anonymous: bool = False

class SurveyResponseCreate(SurveyResponseBase):
    pass

class SurveyResponseResponse(SurveyResponseBase):
    id: int
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WellbeingMetricBase(BaseModel):
    employee_id: int
    metric_type: MetricType
    score: float
    period: str
    factors: Dict[str, Any]
    trend: Optional[str] = None

class WellbeingMetricCreate(WellbeingMetricBase):
    pass

class WellbeingMetricResponse(WellbeingMetricBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class KudosCreate(BaseModel):
    from_employee_id: int
    to_employee_id: int
    message: str
    category: str

class ExperienceScoreResponse(BaseModel):
    employee_id: int
    experience_score: float

class JourneyEvent(BaseModel):
    date: datetime
    event: str
    type: str
    sentiment: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class TrendResponse(BaseModel):
    trend: str
    details: str

class AttritionRiskResponse(BaseModel):
    employee_id: int
    risk_level: str
    name: str

class EngagementDriversResponse(BaseModel):
    drivers: List[str]
