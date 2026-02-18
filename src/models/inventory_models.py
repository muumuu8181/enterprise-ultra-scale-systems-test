from sqlalchemy import Integer, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.models.base import Base

class Item(Base):
    """
    アイテムモデル
    """
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, comment="アイテム名")
    rarity: Mapped[int] = mapped_column(Integer, nullable=False, comment="レアリティ")
    type: Mapped[str] = mapped_column(String, nullable=False, comment="アイテムタイプ")
    stats: Mapped[dict] = mapped_column(JSON, nullable=True, comment="ステータス (JSON)")
    description: Mapped[str] = mapped_column(String, nullable=True, comment="説明")
    icon_url: Mapped[str] = mapped_column(String, nullable=True, comment="アイコンURL")

class UserInventory(Base):
    """
    ユーザーインベントリモデル
    """
    __tablename__ = "user_inventories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False, comment="アイテムID")
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="所持数")
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="取得日時")
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="ロック状態")

    # リレーションシップ
    item = relationship("Item")

class TradeOffer(Base):
    """
    トレードオファーモデル
    """
    __tablename__ = "trade_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, comment="申請者ユーザーID")
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, comment="対象ユーザーID")
    offer_items: Mapped[dict] = mapped_column(JSON, nullable=False, comment="提供アイテム (JSON)")
    request_items: Mapped[dict] = mapped_column(JSON, nullable=False, comment="要求アイテム (JSON)")
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False, comment="ステータス (pending, accepted, rejected, cancelled)")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="有効期限")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="作成日時")
