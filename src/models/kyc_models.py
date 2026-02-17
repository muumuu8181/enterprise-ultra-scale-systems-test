import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base

class KYCStatus(str, enum.Enum):
    """KYCステータスの列挙型"""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class KYCApplication(Base):
    """
    KYC申請モデル

    Attributes:
        id (str): 申請ID (UUID)
        customer_id (str): 顧客ID
        status (KYCStatus): 申請ステータス
        submitted_at (datetime): 申請日時
        verified_at (datetime, optional): 確認日時
        rejection_reason (str, optional): 拒否理由
        documents (dict): 提出書類データ (JSON)
    """
    __tablename__ = "kyc_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, index=True, nullable=False)
    status = Column(Enum(KYCStatus), default=KYCStatus.PENDING, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    documents = Column(JSON, nullable=False, default={})

    def __repr__(self):
        return f"<KYCApplication(id={self.id}, customer_id={self.customer_id}, status={self.status})>"
