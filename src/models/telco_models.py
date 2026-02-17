from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timezone
import enum

class Base(DeclarativeBase):
    pass

class CustomerType(str, enum.Enum):
    PREPAID = "prepaid"
    POSTPAID = "postpaid"
    ENTERPRISE = "enterprise"

class ServiceType(str, enum.Enum):
    MOBILE = "mobile"
    BROADBAND = "broadband"
    VOIP = "voip"
    TV = "tv"

class CallType(str, enum.Enum):
    VOICE = "voice"
    SMS = "sms"
    DATA = "data"

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    customer_type: Mapped[CustomerType] = mapped_column(SAEnum(CustomerType), nullable=False)
    account_status: Mapped[str] = mapped_column(String, nullable=False)
    credit_score: Mapped[int] = mapped_column(Integer, nullable=True)

    services: Mapped[list["Service"]] = relationship("Service", back_populates="customer")

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(SAEnum(ServiceType), nullable=False)
    plan_id: Mapped[str] = mapped_column(String, nullable=False)
    activation_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String, nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="services")
    cdrs: Mapped[list["CDRRecord"]] = relationship("CDRRecord", back_populates="service")

class CDRRecord(Base):
    __tablename__ = "cdr_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    call_type: Mapped[CallType] = mapped_column(SAEnum(CallType), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=True) # Seconds
    bytes: Mapped[int] = mapped_column(Integer, nullable=True) # Bytes for data
    cost: Mapped[float] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    service: Mapped["Service"] = relationship("Service", back_populates="cdrs")
