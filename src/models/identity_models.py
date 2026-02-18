from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class DigitalIdentity(Base):
    """
    Digital Identity Model (DID)
    """
    __tablename__ = "digital_identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    did: Mapped[str] = mapped_column(String, unique=True, index=True)
    public_key: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    credentials: Mapped[List["VerifiableCredential"]] = relationship("VerifiableCredential", back_populates="identity", cascade="all, delete-orphan")
    consents: Mapped[List["ConsentRecord"]] = relationship("ConsentRecord", back_populates="identity", cascade="all, delete-orphan")

class VerifiableCredential(Base):
    """
    Verifiable Credential Model
    """
    __tablename__ = "verifiable_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("digital_identities.id"))
    type: Mapped[str] = mapped_column(String)
    issuer: Mapped[str] = mapped_column(String)
    claims: Mapped[Dict[str, Any]] = mapped_column(JSON)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signature: Mapped[str] = mapped_column(String)

    identity: Mapped["DigitalIdentity"] = relationship("DigitalIdentity", back_populates="credentials")

class ConsentRecord(Base):
    """
    Consent Record Model
    """
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("digital_identities.id"))
    requester: Mapped[str] = mapped_column(String)
    data_types: Mapped[List[str]] = mapped_column(JSON)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    identity: Mapped["DigitalIdentity"] = relationship("DigitalIdentity", back_populates="consents")
