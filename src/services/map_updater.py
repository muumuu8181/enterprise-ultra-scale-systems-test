from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.map_models import MapTile
from typing import Dict, Any, Optional

class MapUpdaterService:

    async def fetch_tile(self, db: AsyncSession, z: int, x: int, y: int) -> Optional[bytes]:
        """
        Fetches a map tile from the database.
        """
        stmt = select(MapTile).where(MapTile.z == z, MapTile.x == x, MapTile.y == y)
        result = await db.execute(stmt)
        tile = result.scalar_one_or_none()
        if tile:
            return tile.data
        return None

    async def invalidate_cache(self, tile_key: str):
        """
        Invalidates the cache for a given tile key.
        This is a placeholder for Redis integration.
        """
        # In a real implementation: await redis.delete(tile_key)
        print(f"Invalidating cache for key: {tile_key}")

    async def broadcast_map_update(self, update_data: Dict[str, Any]):
        """
        Broadcasts a map update event.
        This is a placeholder for Kafka/MQTT integration.
        """
        # In a real implementation: await kafka_producer.send("map_updates", update_data)
        print(f"Broadcasting map update: {update_data}")

    async def update_map_section(self, db: AsyncSession, section_id: str, lane_data: Dict[str, Any], timestamp: str):
        """
        Updates a map section and triggers cache invalidation and broadcast.
        """
        print(f"Updating map section {section_id} with data provided at {timestamp}")

        # Mocking tile calculation based on section_id
        # In reality, we would query which tiles intersect with the section
        affected_tiles = [f"tile_{section_id}_1"]

        for tile_key in affected_tiles:
            await self.invalidate_cache(tile_key)

        payload = {
            "event": "map_update",
            "section_id": section_id,
            "lane_data": lane_data,
            "timestamp": timestamp
        }
        await self.broadcast_map_update(payload)
        return {"status": "updated", "section_id": section_id}

    async def report_incident(self, db: AsyncSession, location: Dict[str, float], type: str, severity: str):
        """
        Reports an incident and broadcasts it.
        """
        print(f"Reporting incident {type} ({severity}) at {location}")

        # TODO: Persist incident report to database
        # incident = Incident(location=location, type=type, severity=severity, ...)
        # db.add(incident)
        # await db.commit()

        payload = {
            "event": "incident_report",
            "location": location,
            "type": type,
            "severity": severity
        }
        await self.broadcast_map_update(payload)
        return {"status": "reported", "type": type}
