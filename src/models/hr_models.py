from datetime import date, datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy import String, Integer, Float, ForeignKey, JSON, Date, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    department: Mapped[str] = mapped_column(String)
    base_salary: Mapped[float] = mapped_column(Float)
    joined_date: Mapped[date] = mapped_column(Date)
    bank_account_number: Mapped[str] = mapped_column(String)

    payrolls: Mapped[List["Payroll"]] = relationship(back_populates="employee")
    bonuses: Mapped[List["Bonus"]] = relationship(back_populates="employee")
    performance_reviews: Mapped[List["PerformanceReview"]] = relationship(back_populates="employee")
    performance_goals: Mapped[List["PerformanceGoal"]] = relationship(back_populates="employee")

class Payroll(Base):
    __tablename__ = "payrolls"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    month: Mapped[str] = mapped_column(String) # YYYY-MM

    basic_salary: Mapped[float] = mapped_column(Float)
    overtime_pay: Mapped[float] = mapped_column(Float, default=0.0)
    deductions: Mapped[float] = mapped_column(Float, default=0.0)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    net_pay: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="PENDING") # PENDING, PROCESSED, PAID

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    employee: Mapped["Employee"] = relationship(back_populates="payrolls")

class Bonus(Base):
    __tablename__ = "bonuses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    amount: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String)
    date_awarded: Mapped[date] = mapped_column(Date, default=date.today)

    employee: Mapped["Employee"] = relationship(back_populates="bonuses")

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    period: Mapped[str] = mapped_column(String) # e.g. "2023-H1"
    ratings: Mapped[Dict] = mapped_column(JSON)
    comments: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    employee: Mapped["Employee"] = relationship(back_populates="performance_reviews")

class PerformanceGoal(Base):
    __tablename__ = "performance_goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    description: Mapped[str] = mapped_column(String)
    deadline: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    employee: Mapped["Employee"] = relationship(back_populates="performance_goals")
