from sqlalchemy import Column, Integer, String, Float, Date, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TIMESTAMP
import enum

Base = declarative_base()

class InvoiceStatus(enum.Enum):
    submitted = "submitted"
    approved = "approved"
    financed = "financed"
    paid = "paid"

class OfferStatus(enum.Enum):
    offered = "offered"
    accepted = "accepted"
    disbursed = "disbursed"
    repaid = "repaid"

class OnboardingStatus(enum.Enum):
    pending = "pending"
    verified = "verified"
    active = "active"
    suspended = "suspended"

class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    buyer_id = Column(Integer, nullable=False)
    invoice_number = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.submitted)
    discount_rate_pct = Column(Float)

    offers = relationship("FinancingOffer", back_populates="invoice")
    supplier = relationship("Supplier", back_populates="invoices")

class FinancingOffer(Base):
    __tablename__ = 'financing_offers'

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    funder_id = Column(Integer, nullable=False)
    advance_rate_pct = Column(Float, nullable=False)
    interest_rate_annual = Column(Float, nullable=False)
    offer_amount = Column(Float, nullable=False)
    tenor_days = Column(Integer, nullable=False)
    status = Column(Enum(OfferStatus), default=OfferStatus.offered)
    offered_at = Column(TIMESTAMP, nullable=False)

    invoice = relationship("Invoice", back_populates="offers")

class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    company_name = Column(String, nullable=False)
    tax_id = Column(String, unique=True, nullable=False)
    credit_score = Column(Integer)
    onboarding_status = Column(Enum(OnboardingStatus), default=OnboardingStatus.pending)
    payment_terms_days = Column(Integer)
    total_financed = Column(Float, default=0.0)

    invoices = relationship("Invoice", back_populates="supplier")
