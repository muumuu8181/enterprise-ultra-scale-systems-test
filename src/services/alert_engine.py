import logging
import asyncio
from datetime import datetime
from src.database import AsyncSessionLocal
from src.models.city_models import Alert, EmergencyIncident, SensorReading

logger = logging.getLogger(__name__)

class AlertEngine:
    """
    アラート生成エンジン: センサーデータを監視し、閾値を超えた場合にアラートや緊急インシデントを生成する
    """
    def __init__(self):
        pass

    async def evaluate_rules(self, sensor_reading: SensorReading) -> bool:
        """
        センサーデータを評価し、必要であればアラートを作成する
        """
        if sensor_reading.value > 0.9:  # 例: 値が0.9を超えたら重大
            severity = "CRITICAL"
            message = f"Sensor {sensor_reading.sensor_id} reported critical value: {sensor_reading.value}"
            await self.create_alert(sensor_reading.sensor_id, severity, message)
            await self.escalate_to_emergency(sensor_reading.sensor_id, "Fire", message)
            return True
        elif sensor_reading.value > 0.7: # 注意
            severity = "WARNING"
            message = f"Sensor {sensor_reading.sensor_id} reported high value: {sensor_reading.value}"
            await self.create_alert(sensor_reading.sensor_id, severity, message)
            return True

        return False

    async def create_alert(self, sensor_id: int, severity: str, message: str):
        """
        データベースにアラートを作成する
        """
        try:
            async with AsyncSessionLocal() as session:
                new_alert = Alert(
                    sensor_id=sensor_id,
                    alert_type="THRESHOLD_EXCEEDED",
                    severity=severity,
                    message=message,
                    triggered_at=datetime.utcnow()
                )
                session.add(new_alert)
                await session.commit()
                logger.info(f"Alert created for sensor {sensor_id}: {severity}")
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")

    async def escalate_to_emergency(self, sensor_id: int, incident_type: str, details: str):
        """
        アラートを緊急インシデントに昇格させる
        """
        try:
            async with AsyncSessionLocal() as session:
                # センサーの位置情報が必要だが、ここでは簡略化のためダミー位置を使用するか、センサーをクエリする
                # 本番ではセンサーIDから位置を特定するロジックが必要

                new_incident = EmergencyIncident(
                    incident_type=incident_type,
                    location="POINT(0 0)", # 実際はセンサーの位置
                    status="REPORTED",
                    priority=1,
                    units_dispatched=[],
                    created_at=datetime.utcnow()
                )
                session.add(new_incident)
                await session.commit()
                logger.info(f"Escalated to emergency incident: {incident_type}")
        except Exception as e:
            logger.error(f"Failed to escalate: {e}")
