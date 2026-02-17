from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class AuthType(str, Enum):
    key = "key"
    oauth2 = "oauth2"
    jwt = "jwt"

class PricingModel(str, Enum):
    free = "free"
    freemium = "freemium"
    paid = "paid"

class APIProduct(Base):
    __tablename__ = "api_products"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    description = Column(String)
    base_url = Column(String)
    auth_type = Column(SAEnum(AuthType))
    pricing_model = Column(SAEnum(PricingModel))

    versions = relationship("APIVersion", back_populates="product")
    subscriptions = relationship("APISubscription", back_populates="product")

class APIVersion(Base):
    __tablename__ = "api_versions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("api_products.id"))
    version = Column(String, index=True)
    openapi_spec = Column(JSON)
    changelog = Column(String)
    deprecated = Column(Boolean, default=False)
    sunset_date = Column(DateTime, nullable=True)

    product = relationship("APIProduct", back_populates="versions")

class APISubscription(Base):
    __tablename__ = "api_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    consumer_id = Column(Integer, index=True)
    product_id = Column(Integer, ForeignKey("api_products.id"))
    plan_id = Column(String)
    api_key = Column(String, unique=True, index=True)
    quota_per_month = Column(Integer)
    usage_this_month = Column(Integer, default=0)

    product = relationship("APIProduct", back_populates="subscriptions")
