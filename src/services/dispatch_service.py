from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.emergency_models import Incident, EmergencyUnit, Dispatch, UnitStatus, IncidentStatus
from typing import List
from datetime import datetime, timezone

class DispatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def auto_dispatch(self, incident: Incident) -> List[EmergencyUnit]:
        """
        Automatically dispatch available units to the incident.
        Finds the nearest available unit.
        """
        # Find nearest available unit using PostGIS distance
        stmt = select(EmergencyUnit).where(
            EmergencyUnit.status == UnitStatus.AVAILABLE
        ).order_by(
            func.ST_Distance(EmergencyUnit.location, incident.location)
        ).limit(1)

        result = await self.db.execute(stmt)
        unit = result.scalar_one_or_none()

        dispatched_units = []
        if unit:
            unit.status = UnitStatus.DISPATCHED

            dispatch = Dispatch(
                incident_id=incident.id,
                unit_id=unit.id,
                dispatched_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            self.db.add(dispatch)

            incident.status = IncidentStatus.DISPATCHED
            dispatched_units.append(unit)

            await self.db.commit()
            await self.db.refresh(unit)

        return dispatched_units

    async def calculate_eta(self, unit_id: int, incident_location) -> int:
        """
        Calculate ETA in seconds.
        Placeholder implementation.
        """
        # In a real scenario, we would use a routing engine (OSRM, Valhalla, etc.)
        return 300  # 5 minutes placeholder

    async def coordinate_multi_agency(self, incident_id: int):
        """
        Coordinate multi-agency response.
        Placeholder implementation.
        """
        # Logic to notify other agencies or escalate
        pass
