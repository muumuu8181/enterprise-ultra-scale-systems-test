from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from src.database import Base

class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    OFFBOARDED = "offboarded"

class SurveyType(str, enum.Enum):
    PULSE = "pulse"
    QUARTERLY = "quarterly"
    EXIT = "exit"

class MetricType(str, enum.Enum):
    STRESS = "stress"
    SATISFACTION = "satisfaction"
    BELONGING = "belonging"
    GROWTH = "growth"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(String, unique=True, index=True)
    name = Column(String)
    department = Column(String, index=True)
    role = Column(String)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    hire_date = Column(DateTime, default=datetime.utcnow)
    engagement_score = Column(Float, default=0.0)
    status = Column(Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE)

    surveys = relationship("SurveyResponse", back_populates="employee")
    metrics = relationship("WellbeingMetric", back_populates="employee")

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True) # Nullable if anonymous? No, anonymous usually means we hide the link, but DB might track it or not. The requirements said `employee_id` is a field.
    survey_type = Column(Enum(SurveyType))
    responses = Column(JSON)
    sentiment_score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    anonymous = Column(Boolean, default=False)

    employee = relationship("Employee", back_populates="surveys")

class WellbeingMetric(Base):
    __tablename__ = "wellbeing_metrics"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    metric_type = Column(Enum(MetricType))
    score = Column(Float)
    period = Column(String)
    factors = Column(JSON)
    trend = Column(String)

    employee = relationship("Employee", back_populates="metrics")
