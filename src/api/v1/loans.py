from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.loan_models import LoanStatus
from src.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])

# Placeholder dependency
async def get_session() -> AsyncSession:
    raise NotImplementedError("Dependency not implemented")

class LoanApplyRequest(BaseModel):
    customer_id: int = Field(default=1)
    amount: Decimal = Field(..., gt=0)
    term_months: int = Field(..., gt=0)
    purpose: str
    interest_rate: Decimal = Field(default=Decimal("0.05"), gt=0, le=1)

class LoanRepayRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)

class LoanRepaymentResponse(BaseModel):
    id: int
    loan_id: int
    due_date: date
    amount: Decimal
    paid_at: Optional[datetime] = None
    penalty: Decimal

    model_config = ConfigDict(from_attributes=True)

class LoanResponse(BaseModel):
    id: int
    customer_id: int
    amount: Decimal
    interest_rate: Decimal
    term_months: int
    purpose: Optional[str] = None
    status: LoanStatus
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

@router.post("/apply", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def apply_loan(request: LoanApplyRequest, session: AsyncSession = Depends(get_session)):
    loan = await LoanService.create_loan(
        session=session,
        customer_id=request.customer_id,
        amount=request.amount,
        interest_rate=request.interest_rate,
        term_months=request.term_months,
        purpose=request.purpose
    )
    return loan

@router.get("/{id}", response_model=LoanResponse)
async def get_loan(id: int, session: AsyncSession = Depends(get_session)):
    loan = await LoanService.get_loan(session, id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan

@router.put("/{id}/approve", response_model=LoanResponse)
async def approve_loan(id: int, session: AsyncSession = Depends(get_session)):
    try:
        loan = await LoanService.approve_loan(session, id)
        return loan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/repay", response_model=LoanResponse)
async def repay_loan(id: int, request: LoanRepayRequest, session: AsyncSession = Depends(get_session)):
    try:
        loan = await LoanService.repay_loan(session, id, request.amount)
        return loan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schedule/{id}", response_model=List[LoanRepaymentResponse])
async def get_schedule(id: int, session: AsyncSession = Depends(get_session)):
    schedule = await LoanService.get_repayment_schedule(session, id)
    return schedule
