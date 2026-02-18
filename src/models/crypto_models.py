from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class CryptoAlgorithm(str, Enum):
    KYBER = "kyber"
    DILITHIUM = "dilithium"
    FALCON = "falcon"
    SPHINCS = "sphincs"

class KeyPair(Base):
    __tablename__ = "key_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, nullable=False)
    public_key: Mapped[str] = mapped_column(String, nullable=False)
    key_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class EncryptedData(Base):
    __tablename__ = "encrypted_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, nullable=False)
    ciphertext_uri: Mapped[str] = mapped_column(String, nullable=False)
    nonce: Mapped[str] = mapped_column(String, nullable=False)
    tag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    key_id: Mapped[int] = mapped_column(ForeignKey("key_pairs.id"), nullable=False)
    original_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    key: Mapped["KeyPair"] = relationship("KeyPair")

class CertificateAuthority(Base):
    __tablename__ = "certificate_authorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    root_cert: Mapped[str] = mapped_column(String, nullable=False)
    intermediate_cert: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crl_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ocsp_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quantum_safe: Mapped[bool] = mapped_column(Boolean, default=True)
