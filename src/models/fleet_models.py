from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime, timezone
from .base import Base

class Fleet(Base):
    """
    フリート情報を管理するモデル
    """
    __tablename__ = 'fleets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, comment='フリート名')
    owner_id = Column(String, nullable=False, comment='所有者ID')
    vehicle_count = Column(Integer, default=0, comment='所属車両数')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='作成日時')

    # リレーションシップ
    vehicles = relationship("FleetVehicle", back_populates="fleet", cascade="all, delete-orphan")

class FleetVehicle(Base):
    """
    フリートに所属する車両のモデル
    """
    __tablename__ = 'fleet_vehicles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fleet_id = Column(Integer, ForeignKey('fleets.id', ondelete="CASCADE"), nullable=False, comment='所属フリートID')
    vehicle_id = Column(String, ForeignKey('vehicles.id'), nullable=False, comment='車両ID')  # 既存のvehiclesテーブルへの外部キー
    model = Column(String, comment='車両モデル')
    status = Column(String, default="active", comment='ステータス (active, maintenance, etc.)')
    current_driver_id = Column(String, nullable=True, comment='現在のドライバーID')
    odometer = Column(Float, default=0.0, comment='総走行距離(km)')

    # リレーションシップ
    fleet = relationship("Fleet", back_populates="vehicles")
    vehicle = relationship("Vehicle")  # 実際の車両データへの参照
    tasks = relationship("FleetTask", back_populates="assigned_vehicle", cascade="all, delete-orphan")

class FleetTask(Base):
    """
    フリート車両への割り当てタスクを管理するモデル
    """
    __tablename__ = 'fleet_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fleet_id = Column(Integer, ForeignKey('fleets.id', ondelete="CASCADE"), nullable=False, comment='関連フリートID')
    vehicle_id = Column(Integer, ForeignKey('fleet_vehicles.id'), nullable=True, comment='割り当て車両ID (FleetVehicle.id)')
    task_type = Column(String, nullable=False, comment='タスクタイプ (delivery, pickup, maintenance, etc.)')
    destination = Column(Geography('POINT', srid=4326), nullable=False, comment='目的地座標')
    priority = Column(Integer, default=0, comment='優先度 (高いほど優先)')
    status = Column(String, default="pending", comment='タスクステータス (pending, in_progress, completed, failed)')
    assigned_at = Column(DateTime(timezone=True), nullable=True, comment='割り当て日時')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='作成日時')

    # リレーションシップ
    assigned_vehicle = relationship("FleetVehicle", back_populates="tasks")

class Vehicle(Base):
    """
    既存のvehiclesテーブルのマッピング (読み取り専用・参照用)
    """
    __tablename__ = 'vehicles'
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, comment='車両ID')
    type = Column(String, nullable=False, comment='車両タイプ')
    last_seen = Column(DateTime(timezone=True), nullable=False, comment='最終確認日時')
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False, comment='現在位置')
