from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from src.models.v2x_models import Base, utcnow

class TollGate(Base):
    """
    電子料金収受所 (Toll Gate) モデル

    Attributes:
        id (int): 内部ID
        gate_id (str): ゲート識別子
        road_name (str): 道路名
        location (Geometry): 位置情報 (POINT)
        lanes (dict): レーン情報 (JSON)
        rate_table (dict): 料金表 (JSON)
    """
    __tablename__ = "toll_gates"

    id: Mapped[int] = mapped_column(primary_key=True)
    gate_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    road_name: Mapped[str] = mapped_column(String)
    # PostGISのPOINT型を使用 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    lanes: Mapped[Dict] = mapped_column(JSON)
    rate_table: Mapped[Dict] = mapped_column(JSON)

class TollTransaction(Base):
    """
    通行料金トランザクションモデル

    Attributes:
        id (int): トランザクションID
        vehicle_id (str): 車両ID
        gate_id (str): ゲートID
        amount (float): 料金
        payment_method (str): 支払い方法
        processed_at (datetime): 処理日時
    """
    __tablename__ = "toll_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    gate_id: Mapped[str] = mapped_column(String, index=True)
    amount: Mapped[float] = mapped_column(Float)
    payment_method: Mapped[str] = mapped_column(String)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class ETCAccount(Base):
    """
    ETCアカウントモデル

    Attributes:
        id (int): アカウントID
        vehicle_id (str): 車両ID
        balance (float): 残高
        auto_recharge_threshold (float): 自動チャージ閾値
        auto_recharge_amount (float): 自動チャージ額
    """
    __tablename__ = "etc_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    auto_recharge_threshold: Mapped[float] = mapped_column(Float, default=1000.0)
    auto_recharge_amount: Mapped[float] = mapped_column(Float, default=5000.0)
