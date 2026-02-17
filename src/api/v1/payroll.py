from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.payroll_service import PayrollService
from pydantic import BaseModel
from src.schemas.hr_schemas import PayrollResponse, BonusResponse, PayrollSummary

router = APIRouter(prefix="/payroll", tags=["payroll"])

class CalculateRequest(BaseModel):
    employee_id: int
    overtime_hours: float = 0.0

class BonusRequest(BaseModel):
    employee_id: int
    amount: float
    reason: str

@router.post("/calculate/{month}", response_model=PayrollResponse)
async def calculate_payroll(month: str, request: CalculateRequest, db: AsyncSession = Depends(get_db)):
    service = PayrollService(db)
    try:
        payroll = await service.calculate_monthly_salary(request.employee_id, month, request.overtime_hours)
        return payroll
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}/{month}", response_model=PayrollResponse)
async def get_payslip(employee_id: int, month: str, db: AsyncSession = Depends(get_db)):
    service = PayrollService(db)
    payroll = await service.generate_payslip(employee_id, month)
    if not payroll:
        raise HTTPException(status_code=404, detail="Payslip not found")
    return payroll

@router.post("/bonuses", response_model=BonusResponse)
async def give_bonus(request: BonusRequest, db: AsyncSession = Depends(get_db)):
    service = PayrollService(db)
    try:
        bonus = await service.award_bonus(request.employee_id, request.amount, request.reason)
        return bonus
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/reports/summary", response_model=PayrollSummary)
async def get_summary(month: str, db: AsyncSession = Depends(get_db)):
    service = PayrollService(db)
    return await service.get_payroll_summary(month)
