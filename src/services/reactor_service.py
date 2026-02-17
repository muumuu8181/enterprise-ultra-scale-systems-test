from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.models.nuclear_models import Reactor, SensorReading, ReactorStatus, SafetySystem, SafetySystemStatus, SensorParameter
from src.schemas.nuclear_schemas import Alarm, SafetyMarginReport, SensorReadingCreate

class ReactorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_sensor_stream(self, readings: List[SensorReadingCreate]) -> List[Alarm]:
        alarms = []
        for reading_data in readings:
            # Create DB object
            db_reading = SensorReading(
                reactor_id=reading_data.reactor_id,
                sensor_id=reading_data.sensor_id,
                parameter=reading_data.parameter,
                value=reading_data.value,
                timestamp=reading_data.timestamp or datetime.now(timezone.utc),
                is_alarm=reading_data.is_alarm
            )
            self.db.add(db_reading)

            # Check thresholds
            threshold = 0.0
            message = ""
            is_critical = False

            if reading_data.parameter == SensorParameter.TEMPERATURE:
                threshold = 1000.0  # Safe max temp
                if reading_data.value > threshold:
                    message = f"Temperature {reading_data.value} exceeds {threshold}"
                    is_critical = True
            elif reading_data.parameter == SensorParameter.PRESSURE:
                threshold = 200.0   # Safe max pressure
                if reading_data.value > threshold:
                    message = f"Pressure {reading_data.value} exceeds {threshold}"
                    is_critical = True

            if is_critical:
                alarms.append(Alarm(
                    sensor_id=reading_data.sensor_id,
                    parameter=reading_data.parameter,
                    current_value=reading_data.value,
                    threshold=threshold,
                    timestamp=reading_data.timestamp or datetime.now(timezone.utc),
                    message=message
                ))
                db_reading.is_alarm = True

        await self.db.commit()
        return alarms

    async def evaluate_safety_margins(self, reactor_id: int) -> SafetyMarginReport:
        stmt = select(Reactor).where(Reactor.id == reactor_id)
        result = await self.db.execute(stmt)
        reactor = result.scalar_one_or_none()

        if not reactor:
            raise ValueError(f"Reactor {reactor_id} not found")

        # Example calculation
        # Max core temp = 1200
        # Max thermal power = rated power * 1.05

        max_core_temp = 1200.0
        current_core_temp = reactor.core_temperature
        core_temp_margin = max_core_temp - current_core_temp

        thermal_power_margin = (reactor.thermal_power_mw * 0.05) # Assume current is close to rated

        status = "SAFE"
        if core_temp_margin < 50:
            status = "CRITICAL"
        elif core_temp_margin < 200:
            status = "WARNING"

        return SafetyMarginReport(
            reactor_id=reactor_id,
            timestamp=datetime.now(timezone.utc),
            core_temp_margin=core_temp_margin,
            thermal_power_margin=thermal_power_margin,
            overall_status=status
        )

    async def calculate_capacity_factor(self, reactor_id: int, period: str) -> float:
        # Placeholder
        # In a real system, query operational hours vs total hours in `period`
        return 0.95
