from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.loan_models import Loan, LoanRepayment, LoanStatus

class LoanService:
    @staticmethod
    def calculate_monthly_payment(principal: Decimal, annual_interest_rate: Decimal, term_months: int) -> Decimal:
        """
        Calculates the monthly payment using the equal principal and interest method.
        PMT = P * r * (1 + r)^n / ((1 + r)^n - 1)
        """
        if term_months <= 0:
            raise ValueError("Term months must be greater than 0")

        if annual_interest_rate == 0:
            return principal / Decimal(term_months)

        monthly_rate = annual_interest_rate / Decimal(12)

        numerator = principal * monthly_rate * ((1 + monthly_rate) ** term_months)
        denominator = ((1 + monthly_rate) ** term_months) - 1

        payment = numerator / denominator
        # Round to 2 decimal places
        return payment.quantize(Decimal("0.01"))

    @staticmethod
    async def create_loan(session: AsyncSession, customer_id: int, amount: Decimal, interest_rate: Decimal, term_months: int, purpose: str) -> Loan:
        loan = Loan(
            customer_id=customer_id,
            amount=amount,
            interest_rate=interest_rate,
            term_months=term_months,
            purpose=purpose,
            status=LoanStatus.PENDING
        )
        session.add(loan)
        await session.commit()
        await session.refresh(loan)
        return loan

    @staticmethod
    async def get_loan(session: AsyncSession, loan_id: int) -> Optional[Loan]:
        result = await session.execute(select(Loan).where(Loan.id == loan_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def approve_loan(session: AsyncSession, loan_id: int) -> Loan:
        loan = await LoanService.get_loan(session, loan_id)
        if not loan:
            raise ValueError("Loan not found")

        if loan.status != LoanStatus.PENDING:
            raise ValueError(f"Loan status is {loan.status}, cannot approve.")

        loan.status = LoanStatus.APPROVED
        loan.approved_at = datetime.now(timezone.utc)

        # Generate schedule
        await LoanService.generate_repayment_schedule(session, loan)

        await session.commit()
        await session.refresh(loan)
        return loan

    @staticmethod
    def _add_months(start_date: date, months: int) -> date:
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(start_date.day, [31, 29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)

    @staticmethod
    async def generate_repayment_schedule(session: AsyncSession, loan: Loan):
        """
        Generates LoanRepayment records.
        """
        principal = loan.amount
        rate = loan.interest_rate
        term = loan.term_months
        start_date = loan.approved_at.date() if loan.approved_at else date.today()

        monthly_payment = LoanService.calculate_monthly_payment(principal, rate, term)

        balance = principal
        monthly_rate = rate / Decimal(12)

        for i in range(1, term + 1):
            interest = balance * monthly_rate
            principal_payment = monthly_payment - interest

            # Adjust last payment to handle rounding
            if i == term:
                payment_amount = balance + interest
            else:
                payment_amount = monthly_payment

            balance -= (payment_amount - interest)

            due_date = LoanService._add_months(start_date, i)

            repayment = LoanRepayment(
                loan_id=loan.id,
                due_date=due_date,
                amount=payment_amount.quantize(Decimal("0.01"))
            )
            session.add(repayment)

    @staticmethod
    async def get_repayment_schedule(session: AsyncSession, loan_id: int) -> List[LoanRepayment]:
        result = await session.execute(select(LoanRepayment).where(LoanRepayment.loan_id == loan_id).order_by(LoanRepayment.due_date))
        return result.scalars().all()

    @staticmethod
    async def repay_loan(session: AsyncSession, loan_id: int, amount: Decimal) -> Loan:
        """
        Applies a repayment amount to the earliest unpaid installments.
        """
        loan = await LoanService.get_loan(session, loan_id)
        if not loan:
            raise ValueError("Loan not found")

        unpaid_repayments_result = await session.execute(
            select(LoanRepayment)
            .where(LoanRepayment.loan_id == loan_id, LoanRepayment.paid_at.is_(None))
            .order_by(LoanRepayment.due_date)
        )
        repayments = unpaid_repayments_result.scalars().all()

        # Calculate exactly which installments can be paid
        cumulative_amount = Decimal("0")
        installments_to_pay = []

        for repayment in repayments:
            if cumulative_amount + repayment.amount <= amount:
                cumulative_amount += repayment.amount
                installments_to_pay.append(repayment)
            else:
                break

        if cumulative_amount != amount:
            raise ValueError("Amount must match the sum of one or more installments exactly.")

        if not installments_to_pay:
             # Should not happen given check above, unless amount is 0 which is invalid via API
             # But if amount < first installment
             raise ValueError("Amount is less than the next due installment.")

        for repayment in installments_to_pay:
            repayment.paid_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(loan)

        # Check if fully paid
        all_unpaid_result = await session.execute(
            select(LoanRepayment)
            .where(LoanRepayment.loan_id == loan_id, LoanRepayment.paid_at.is_(None))
        )
        if not all_unpaid_result.scalar_one_or_none():
             loan.status = LoanStatus.PAID_OFF
             await session.commit()

        return loan

    @staticmethod
    async def check_delinquency(session: AsyncSession, loan_id: int) -> bool:
        """
        Checks if the loan has any overdue payments.
        """
        today = date.today()
        result = await session.execute(
            select(LoanRepayment)
            .where(
                LoanRepayment.loan_id == loan_id,
                LoanRepayment.paid_at.is_(None),
                LoanRepayment.due_date < today
            )
        )
        overdue = result.scalars().first()
        if overdue:
             loan = await LoanService.get_loan(session, loan_id)
             if loan and loan.status not in [LoanStatus.DEFAULTED, LoanStatus.PAID_OFF, LoanStatus.REJECTED]:
                 loan.status = LoanStatus.DEFAULTED
                 await session.commit()
             return True
        return False
