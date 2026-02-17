import enum
from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
# Accountモデルのインポートは循環参照を避けるためにTYPE_CHECKING内で行うか、文字列参照を利用します
# ここでは文字列参照を利用します

class CardStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CANCELLED = "cancelled"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DECLINED = "declined"

class Card(Base):
    """
    クレジットカード/デビットカードモデル
    """
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)

    # セキュリティ上の理由からカード番号はマスク化して保存 (例: ************1234)
    card_number_masked: Mapped[str] = mapped_column(String, nullable=False)

    # 有効期限 (MM/YY)
    expiry_date: Mapped[str] = mapped_column(String(5), nullable=False)

    # CVVはハッシュ化して保存
    cvv_hash: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[CardStatus] = mapped_column(Enum(CardStatus), default=CardStatus.ACTIVE, nullable=False)

    # 取引制限
    daily_limit: Mapped[float] = mapped_column(Float, default=500000.0)
    monthly_limit: Mapped[float] = mapped_column(Float, default=2000000.0)

    # リレーションシップ
    transactions: Mapped[List["CardTransaction"]] = relationship(back_populates="card", cascade="all, delete-orphan")

class CardTransaction(Base):
    """
    カード取引履歴モデル
    """
    __tablename__ = "card_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)

    merchant: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="JPY", nullable=False)

    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)

    processed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # リレーションシップ
    card: Mapped["Card"] = relationship(back_populates="transactions")
