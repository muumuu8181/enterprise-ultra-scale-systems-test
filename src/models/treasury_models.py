from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.db.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AssetType(str, Enum):
    TOKEN = "token"
    NFT = "nft"
    STABLECOIN = "stablecoin"

class GrantStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    FUNDED = "funded"
    REJECTED = "rejected"

class TransactionType(str, Enum):
    PAYMENT = "payment"
    SWAP = "swap"
    DELEGATE = "delegate"

class TreasuryAsset(Base):
    __tablename__ = "treasury_assets"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(String, index=True, nullable=False)
    asset_type = Column(SAEnum(AssetType), nullable=False)
    token_address = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    usd_value = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now)

    history = relationship("TreasuryHistory", back_populates="asset", cascade="all, delete-orphan")

class GrantApplication(Base):
    __tablename__ = "grant_applications"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(String, index=True, nullable=False)
    applicant_address = Column(String, nullable=False)
    requested_amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    milestones = Column(JSON, nullable=True) # List of objects: [{"id": 1, "description": "MVP", "status": "pending"}]
    status = Column(SAEnum(GrantStatus), default=GrantStatus.SUBMITTED)
    created_at = Column(DateTime, default=utc_now)

class MultisigTransaction(Base):
    __tablename__ = "multisig_transactions"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(String, index=True, nullable=False)
    tx_type = Column(SAEnum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    recipient = Column(String, nullable=False)
    signers_required = Column(Integer, default=2)
    signatures = Column(JSON, default=list) # List of signer addresses
    executed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

class TreasuryHistory(Base):
    __tablename__ = "treasury_history"

    id = Column(Integer, primary_key=True, index=True)
    dao_id = Column(String, index=True, nullable=False)
    asset_id = Column(Integer, ForeignKey("treasury_assets.id"), nullable=False)
    timestamp = Column(DateTime, default=utc_now)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    tx_ref = Column(String, nullable=True) # Optional reference to a transaction hash or ID

    asset = relationship("TreasuryAsset", back_populates="history")
