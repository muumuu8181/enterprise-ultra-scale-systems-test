from datetime import datetime
from typing import List, Optional, Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.elements import WKTElement

from src.models.rsu_models import RSUnit, RSUCoverage

class RSUManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_rsu(self, rsu_id: str, location_wkt: str, coverage_radius: float, firmware_version: str) -> RSUnit:
        """Creates a new RSU unit."""
        # Using WKTElement to wrap the location string
        point = WKTElement(location_wkt, srid=4326)

        new_rsu = RSUnit(
            rsu_id=rsu_id,
            location=point,
            coverage_radius=coverage_radius,
            firmware_version=firmware_version,
            status="offline"
        )
        self.session.add(new_rsu)
        await self.session.commit()
        await self.session.refresh(new_rsu)
        return new_rsu

    async def get_rsu(self, rsu_id_pk: int) -> Optional[RSUnit]:
        """Retrieves an RSU by its primary key ID."""
        stmt = select(RSUnit).where(RSUnit.id == rsu_id_pk)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_rsu_status(self, rsu_id_pk: int) -> Optional[dict]:
        """Returns the status dictionary for an RSU."""
        rsu = await self.get_rsu(rsu_id_pk)
        if not rsu:
            return None
        return {
            "id": rsu.id,
            "status": rsu.status,
            "last_heartbeat": rsu.last_heartbeat,
            "firmware_version": rsu.firmware_version
        }

    async def deploy_config(self, rsu_id_pk: int, broadcast_interval_ms: Optional[int] = None, power_level_dbm: Optional[float] = None) -> Optional[RSUnit]:
        """Updates RSU configuration."""
        values = {}
        if broadcast_interval_ms is not None:
            values["broadcast_interval_ms"] = broadcast_interval_ms
        if power_level_dbm is not None:
            values["power_level_dbm"] = power_level_dbm

        if not values:
            return await self.get_rsu(rsu_id_pk)

        stmt = update(RSUnit).where(RSUnit.id == rsu_id_pk).values(**values)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_rsu(rsu_id_pk)

    async def update_firmware(self, rsu_id_pk: int, package_id: str) -> Optional[RSUnit]:
        """Updates firmware version for an RSU."""
        stmt = update(RSUnit).where(RSUnit.id == rsu_id_pk).values(firmware_version=package_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_rsu(rsu_id_pk)

    async def monitor_health(self, rsu_id_pk: int) -> Optional[RSUnit]:
        """Updates the heartbeat timestamp for an RSU."""
        stmt = update(RSUnit).where(RSUnit.id == rsu_id_pk).values(
            last_heartbeat=func.now(),
            status="online"
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_rsu(rsu_id_pk)

    async def calculate_coverage(self, bounds: str) -> List[RSUCoverage]:
        """
        Retrieves coverage polygons within the given bounds.
        bounds format: 'min_lon,min_lat,max_lon,max_lat'
        """
        try:
            min_x, min_y, max_x, max_y = map(float, bounds.split(','))
            bbox_wkt = f"POLYGON(({min_x} {min_y}, {min_x} {max_y}, {max_x} {max_y}, {max_x} {min_y}, {min_x} {min_y}))"

            stmt = select(RSUCoverage).where(
                func.ST_Intersects(RSUCoverage.covered_area, func.ST_GeomFromText(bbox_wkt, 4326))
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except ValueError:
            # Handle invalid bounds format gracefully
            return []
