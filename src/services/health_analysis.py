from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.wearable_models import HealthMetric, HealthAlert, WearableDevice, AlertType, MetricType

class HRVReport(BaseModel):
    user_id: str
    rmssd: float
    sdnn: float
    timestamp: datetime
    metrics_count: int

async def analyze_hrv(user_id: str, db: AsyncSession, window_hours: int = 24) -> HRVReport:
    """
    Analyzes Heart Rate Variability for the given user over the specified window.
    Currently returns a mock report.
    """
    # In a real implementation, we would fetch heart rate intervals (RR intervals)
    # and calculate RMSSD and SDNN.
    # For this task, we will return a simulated report.

    return HRVReport(
        user_id=user_id,
        rmssd=55.0,  # Mock value
        sdnn=60.0,   # Mock value
        timestamp=datetime.now(timezone.utc),
        metrics_count=100
    )

async def detect_anomaly(metric: HealthMetric, db: AsyncSession) -> Optional[HealthAlert]:
    """
    Detects anomalies in the provided HealthMetric.
    If an anomaly is detected, creates and returns a HealthAlert.
    """
    alert_type = None
    severity = "medium"

    if metric.metric_type == MetricType.heart_rate:
        if metric.value > 180 or metric.value < 40:
            alert_type = AlertType.abnormal_hr
            severity = "high"
    elif metric.metric_type == MetricType.spo2:
        if metric.value < 90:
            alert_type = AlertType.low_spo2
            severity = "critical"
    elif metric.metric_type == MetricType.glucose:
        if metric.value > 300 or metric.value < 50:
            alert_type = AlertType.high_glucose
            severity = "high"

    # Check for fall detection (usually a specific event, not a metric value, but mapped here if needed)
    # If metric_type was 'fall_detected' (not in MetricType enum but handled via logic)

    if alert_type:
        # Fetch device to get user_id
        result = await db.execute(select(WearableDevice).where(WearableDevice.id == metric.device_id))
        device = result.scalar_one_or_none()

        if device:
            alert = HealthAlert(
                user_id=device.user_id,
                alert_type=alert_type,
                severity=severity,
                acknowledged=False
            )
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
            return alert

    return None

async def generate_wellness_score(user_id: str, db: AsyncSession) -> float:
    """
    Generates a wellness score (0-100) for the user based on recent metrics.
    """
    # Mock implementation
    return 85.5
