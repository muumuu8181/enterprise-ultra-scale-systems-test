from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class NFTToken(Base):
    """
    NFTトークンモデル
    """
    __tablename__ = "nft_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token_id: Mapped[str] = mapped_column(String, index=True)
    contract_address: Mapped[str] = mapped_column(String)
    owner_address: Mapped[str] = mapped_column(String, index=True)
    metadata_uri: Mapped[str] = mapped_column(String)
    last_price_eth: Mapped[float] = mapped_column(Float, nullable=True)

    # リレーションシップ (VirtualLandなどと関連付け)
    virtual_land: Mapped[Optional["VirtualLand"]] = relationship("VirtualLand", back_populates="nft_token", uselist=False)

class VirtualLand(Base):
    """
    仮想空間の土地モデル
    """
    __tablename__ = "virtual_lands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parcel_x: Mapped[int] = mapped_column(Integer, index=True)
    parcel_y: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[str] = mapped_column(String, index=True) # ユーザーIDまたはウォレットアドレス
    nft_token_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("nft_tokens.id"), nullable=True)
    development_status: Mapped[str] = mapped_column(String, default="undeveloped") # developed, constructing, etc.

    nft_token: Mapped[Optional["NFTToken"]] = relationship("NFTToken", back_populates="virtual_land")

class Marketplace(Base):
    """
    マーケットプレイス出品モデル
    """
    __tablename__ = "marketplace_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[str] = mapped_column(String, index=True)
    asset_id: Mapped[int] = mapped_column(Integer) # NFTToken.id または VirtualLand.id (ここではNFT IDを想定)
    price_tokens: Mapped[float] = mapped_column(Float)
    listing_type: Mapped[str] = mapped_column(String) # fixed, auction
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    """
    取引履歴モデル
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    buyer_id: Mapped[str] = mapped_column(String, index=True)
    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplace_listings.id"))
    amount: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="completed")
