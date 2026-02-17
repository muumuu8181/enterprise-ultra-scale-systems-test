from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import String, Integer, Float, DateTime, Boolean, LargeBinary, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from geoalchemy2 import Geometry

class Base(AsyncAttrs, DeclarativeBase):
    """
    SQLAlchemy 2.0のベースクラス
    AsyncAttrsを使用して非同期操作をサポート
    """
    pass

def utcnow():
    return datetime.now(timezone.utc)

class Vehicle(Base):
    """
    車両情報を管理するモデル

    Attributes:
        id (int): 内部ID
        vehicle_id (str): 車両識別子
        station_type (int): ステーションタイプ (ITS station type)
        location (Geometry): 現在位置 (POINT)
        speed (float): 速度 (m/s)
        heading (float): 進行方向 (度)
        updated_at (datetime): 更新日時
    """
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    station_type: Mapped[int] = mapped_column(Integer)
    # PostGISのPOINT型を使用 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    speed: Mapped[float] = mapped_column(Float)
    heading: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

class CAMMessage(Base):
    """
    CAM (Cooperative Awareness Message) のログモデル

    Attributes:
        id (int): メッセージID
        vehicle_id (str): 送信元車両ID
        station_id (int): ステーションID
        latitude (float): 緯度
        longitude (float): 経度
        speed (float): 速度
        heading (float): 進行方向
        timestamp (datetime): メッセージ生成時刻
        raw_bytes (bytes): メッセージの生データ
    """
    __tablename__ = "cam_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    station_id: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    speed: Mapped[float] = mapped_column(Float)
    heading: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    raw_bytes: Mapped[bytes] = mapped_column(LargeBinary)

class DENMMessage(Base):
    """
    DENM (Decentralized Environmental Notification Message) のモデル
    危険情報などを保持

    Attributes:
        id (int): メッセージID
        origin_station_id (int): 発生元ステーションID
        cause_code (int): 原因コード
        sub_cause_code (int): 詳細原因コード
        location (Geometry): 発生位置 (POINT)
        validity_duration (int): 有効期間 (秒)
        created_at (datetime): 作成日時
    """
    __tablename__ = "denm_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    origin_station_id: Mapped[int] = mapped_column(Integer)
    cause_code: Mapped[int] = mapped_column(Integer)
    sub_cause_code: Mapped[int] = mapped_column(Integer)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    validity_duration: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class SPATMessage(Base):
    """
    SPAT (Signal Phase and Timing) のモデル
    信号機の位相とタイミング情報

    Attributes:
        id (int): メッセージID
        intersection_id (int): 交差点ID
        phase_states (dict): 各フェーズの状態 (JSON)
        timing_info (dict): タイミング情報 (JSON)
        timestamp (datetime): メッセージ生成時刻
    """
    __tablename__ = "spat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    intersection_id: Mapped[int] = mapped_column(Integer, index=True)
    phase_states: Mapped[dict] = mapped_column(JSON)
    timing_info: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime)

class PKICertificate(Base):
    """
    PKI証明書モデル

    Attributes:
        id (int): 証明書ID
        vehicle_id (str): 車両ID
        cert_type (str): 証明書タイプ (enrollment, pseudonym, etc.)
        serial_number (str): シリアル番号
        valid_from (datetime): 有効開始日時
        valid_until (datetime): 有効終了日時
        revoked (bool): 失効フラグ
    """
    __tablename__ = "pki_certificates"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    cert_type: Mapped[str] = mapped_column(String)
    serial_number: Mapped[str] = mapped_column(String, unique=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime)
    valid_until: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

class OTAPackage(Base):
    """
    OTAパッケージモデル

    Attributes:
        id (int): パッケージID
        version (str): バージョン
        target_ecu (str): 対象ECU
        checksum (str): チェックサム
        status (str): ステータス
        created_at (datetime): 作成日時
    """
    __tablename__ = "ota_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String)
    target_ecu: Mapped[str] = mapped_column(String)
    checksum: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending") # pending, deploying, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
