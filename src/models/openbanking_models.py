import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List

from sqlalchemy import String, JSON, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

class ConsentStatus(str, PyEnum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[str] = mapped_column(String, nullable=False)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    scopes: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(Enum(ConsentStatus), default=ConsentStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    audit_logs: Mapped[List["ConsentAuditLog"]] = relationship("ConsentAuditLog", back_populates="consent", cascade="all, delete-orphan")

class ConsentAuditLog(Base):
    __tablename__ = "consent_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("consents.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    consent: Mapped["Consent"] = relationship("Consent", back_populates="audit_logs")
