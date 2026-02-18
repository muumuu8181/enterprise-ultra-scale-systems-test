from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.hr_models import Employee, Payroll, Bonus
from datetime import datetime, timezone

class PayrollService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_tax(self, gross_salary: float) -> float:
        # Simple progressive tax logic for demo
        # Assuming standard tax brackets
        if gross_salary < 300000:
            return gross_salary * 0.1
        else:
            return 30000 + (gross_salary - 300000) * 0.2

    async def calculate_monthly_salary(self, employee_id: int, month: str, overtime_hours: float = 0.0) -> Payroll:
        result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        employee = result.scalar_one_or_none()
        if not employee:
            raise ValueError(f"Employee with id {employee_id} not found")

        # Basic calculation
        # Assuming standard 160 working hours for overtime base calculation
        overtime_rate = (employee.base_salary / 160) * 1.5
        overtime_pay = overtime_hours * overtime_rate
        gross_salary = employee.base_salary + overtime_pay

        # Deductions (Social Insurance etc. - simplified 15%)
        deductions = gross_salary * 0.15

        taxable_income = gross_salary - deductions
        tax = await self.calculate_tax(taxable_income)
        net_pay = taxable_income - tax

        payroll = Payroll(
            employee_id=employee_id,
            month=month,
            basic_salary=employee.base_salary,
            overtime_pay=overtime_pay,
            deductions=deductions,
            tax=tax,
            net_pay=net_pay,
            status="PROCESSED"
        )
        self.db.add(payroll)
        await self.db.commit()
        await self.db.refresh(payroll)
        return payroll

    async def generate_payslip(self, employee_id: int, month: str) -> Payroll:
        result = await self.db.execute(
            select(Payroll).where(Payroll.employee_id == employee_id, Payroll.month == month)
        )
        payroll = result.scalar_one_or_none()
        return payroll

    async def process_bank_transfer(self, payroll_id: int) -> bool:
        result = await self.db.execute(select(Payroll).where(Payroll.id == payroll_id))
        payroll = result.scalar_one_or_none()
        if not payroll:
            return False

        # Mock transfer logic
        # In real system, call banking API
        # Here we just update status

        payroll.status = "PAID"
        await self.db.commit()
        await self.db.refresh(payroll)
        return True

    async def award_bonus(self, employee_id: int, amount: float, reason: str) -> Bonus:
        # Validate employee exists
        result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        if not result.scalar_one_or_none():
             raise ValueError(f"Employee with id {employee_id} not found")

        bonus = Bonus(employee_id=employee_id, amount=amount, reason=reason)
        self.db.add(bonus)
        await self.db.commit()
        await self.db.refresh(bonus)
        return bonus

    async def get_payroll_summary(self, month: str):
        result = await self.db.execute(select(Payroll).where(Payroll.month == month))
        payrolls = result.scalars().all()

        total_salary = sum(p.basic_salary for p in payrolls)
        total_tax = sum(p.tax for p in payrolls)
        total_net = sum(p.net_pay for p in payrolls)

        return {
            "month": month,
            "total_employees": len(payrolls),
            "total_basic_salary": total_salary,
            "total_tax": total_tax,
            "total_net_pay": total_net
        }
