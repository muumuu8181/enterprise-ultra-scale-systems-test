from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base

class SanctionsCheck(Base):
    """
    制裁リスト照合結果モデル
    OFACや国連制裁リストとの照合履歴を管理します。
    """
    __tablename__ = "sanctions_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")
    customer_id: Mapped[str] = mapped_column(String, nullable=False, comment="顧客ID")
    status: Mapped[str] = mapped_column(String, nullable=False, comment="ステータス (CLEAR, MATCHED, PENDING)")
    matched_list: Mapped[Optional[str]] = mapped_column(String, nullable=True, comment="一致したリスト名 (OFAC, UNなど)")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="照合日時"
    )

class SAR(Base):
    """
    疑わしい取引報告書 (Suspicious Activity Report) モデル
    検知された疑わしい取引の報告データを管理します。
    """
    __tablename__ = "sars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")
    customer_id: Mapped[str] = mapped_column(String, nullable=False, comment="顧客ID")
    transactions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="関連取引データ (JSON)")
    risk_indicators: Mapped[List[str]] = mapped_column(JSON, nullable=False, comment="リスク指標リスト (JSON)")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="提出日時"
    )
