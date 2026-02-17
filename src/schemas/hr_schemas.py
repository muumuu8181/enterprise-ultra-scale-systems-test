from datetime import date, datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

class EmployeeBase(BaseModel):
    name: str
    department: str
    base_salary: float
    joined_date: date
    bank_account_number: str

class EmployeeResponse(EmployeeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PayrollBase(BaseModel):
    employee_id: int
    month: str
    basic_salary: float
    overtime_pay: float = 0.0
    deductions: float = 0.0
    tax: float = 0.0
    net_pay: float = 0.0
    status: str

class PayrollResponse(PayrollBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BonusBase(BaseModel):
    employee_id: int
    amount: float
    reason: str
    date_awarded: date = Field(default_factory=date.today)

class BonusResponse(BonusBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PerformanceReviewBase(BaseModel):
    employee_id: int
    period: str
    ratings: Dict[str, int]
    comments: str

class PerformanceReviewResponse(PerformanceReviewBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PerformanceGoalBase(BaseModel):
    description: str
    deadline: date
    status: str = "PENDING"

class PerformanceGoalResponse(PerformanceGoalBase):
    id: int
    employee_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PayrollSummary(BaseModel):
    month: str
    total_employees: int
    total_basic_salary: float
    total_tax: float
    total_net_pay: float
