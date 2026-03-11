from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum as SAEnum, Boolean
import enum
from src.database import Base
from datetime import datetime

class GoalType(str, enum.Enum):
    emergency_fund = "emergency_fund"
    vacation = "vacation"
    home = "home"
    retirement = "retirement"

class AssetType(str, enum.Enum):
    stock = "stock"
    etf = "etf"
    mutual_fund = "mutual_fund"
    crypto = "crypto"
    bond = "bond"

class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    goal_type = Column(SAEnum(GoalType), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    deadline = Column(DateTime, nullable=False)
    monthly_contribution = Column(Float, default=0.0)

class InvestmentHolding(Base):
    __tablename__ = "investment_holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    asset_type = Column(SAEnum(AssetType), nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)

class TaxSummary(Base):
    __tablename__ = "tax_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tax_year = Column(Integer, nullable=False)
    income_types = Column(JSON, nullable=False)
    deductions = Column(JSON, nullable=False)
    estimated_tax = Column(Float, nullable=False)
    export_ready = Column(Boolean, default=False)
