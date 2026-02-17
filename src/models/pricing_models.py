from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from src.database import Base

class RuleType(str, enum.Enum):
    MARKDOWN = "markdown"
    DYNAMIC = "dynamic"
    BUNDLE = "bundle"
    SURGE = "surge"

class PriceChangeReason(str, enum.Enum):
    RULE = "rule"
    MANUAL = "manual"
    COMPETITOR = "competitor"
    DEMAND = "demand"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, index=True)
    base_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    competitor_prices = Column(JSON, default={})
    elasticity_score = Column(Float, default=1.0)
    last_repriced = Column(DateTime, default=datetime.utcnow)

    pricing_rules = relationship("PricingRule", back_populates="product")
    price_changes = relationship("PriceChange", back_populates="product")

class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False)
    conditions = Column(JSON, default={})
    min_price = Column(Float)
    max_price = Column(Float)
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True)

    product = relationship("Product", back_populates="pricing_rules")

class PriceChange(Base):
    __tablename__ = "price_changes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    reason = Column(Enum(PriceChangeReason), nullable=False)
    impact_forecast = Column(Float)  # Forecasted impact (e.g. revenue change)
    approved_by = Column(String, nullable=True)
    effective_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_changes")
