import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

class DeviceType(str, enum.Enum):
    smartwatch = "smartwatch"
    fitness_band = "fitness_band"
    cgm = "cgm"
    ecg = "ecg"

class MetricType(str, enum.Enum):
    heart_rate = "heart_rate"
    spo2 = "spo2"
    steps = "steps"
    calories = "calories"
    sleep = "sleep"
    glucose = "glucose"

class AlertType(str, enum.Enum):
    abnormal_hr = "abnormal_hr"
    low_spo2 = "low_spo2"
    high_glucose = "high_glucose"
    fall_detected = "fall_detected"

class WearableDevice(Base):
    __tablename__ = "wearable_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    device_type: Mapped[DeviceType] = mapped_column(Enum(DeviceType))
    serial: Mapped[str] = mapped_column(String, unique=True, index=True)
    firmware_version: Mapped[str] = mapped_column(String)
    last_sync: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    battery_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    metrics: Mapped[List["HealthMetric"]] = relationship(back_populates="device", cascade="all, delete-orphan")

class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("wearable_devices.id"))
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType))
    value: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    quality_score: Mapped[int] = mapped_column(Integer)

    device: Mapped["WearableDevice"] = relationship(back_populates="metrics")

class HealthAlert(Base):
    __tablename__ = "health_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    severity: Mapped[str] = mapped_column(String)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
