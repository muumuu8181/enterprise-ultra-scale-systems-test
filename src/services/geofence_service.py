from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography
from src.models.location_models import GeofenceZone, GeofenceEvent, UserLocation
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

class POI(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    category: Optional[str] = None

async def check_geofences(db: AsyncSession, user_id: str, lat: float, lon: float) -> List[GeofenceEvent]:
    """
    Check geofences for a user at a given location and generate events.
    """
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)

    # 1. Find all zones containing the point
    # Note: For circles (stored as Point + radius_m), we use ST_DWithin.
    # For Polygons, we use ST_Contains.
    # We can use ST_DWithin with radius 0 for polygons if we handle types separately,
    # but simplest is to check both conditions or rely on geometry type.
    # Since we store both as Geometry, we can try a combined query.

    # However, for 'circle' type, the geometry is likely the center point.
    # So we need to handle 'circle' vs 'polygon' logic.

    # Since we can't easily mix Polygon contains and Point dwithin in one simple ORM query
    # without complex SQL logic (CASE WHEN ...), and we might have few zones,
    # we can iterate or build a complex query.
    # For "ultra-scale", we should do it in SQL.

    # SQL approach:
    # WHERE (zone_type = 'polygon' AND ST_Contains(geometry, point))
    #    OR (zone_type = 'circle' AND ST_DWithin(geometry::geography, point::geography, radius_m))

    query = select(GeofenceZone).where(
        func.ST_Contains(GeofenceZone.geometry, point) |
        (
            (GeofenceZone.zone_type == 'circle') &
            func.ST_DWithin(
                func.CAST(GeofenceZone.geometry, Geography),
                func.CAST(point, Geography),
                GeofenceZone.radius_m
            )
        )
    )

    # Note: ST_Contains for a Point geometry (center of circle) and a Point (user) will only match if exact.
    # So the OR condition handles the circle case correctly (assuming circle geometry is Point).
    # If circle geometry is a Polygon approximation, ST_Contains works for both.
    # We'll assume the SQL query above covers both cases (Circle as Point+Radius, Polygon as Polygon).

    result = await db.execute(query)
    current_zones = result.scalars().all()
    current_zone_ids = {z.id for z in current_zones}

    new_events = []

    # 2. Get status of these zones (and others) for the user
    # We need the latest event for each relevant zone to determine if we just entered or exited.
    # We look at "current_zones" (candidates for ENTER/DWELL) and "recently active zones" (candidates for EXIT).

    # To find "was inside", we query for latest "enter" or "exit" for this user.
    # This is complex to do efficiently in one query for all zones.
    # We will fetch latest event for each current_zone, and also find zones where user is currently "inside".

    # Strategy: Find all zones where the last event was 'enter'.
    # This requires a subquery or window function.

    # Subquery to find latest event ID per zone for this user
    subq = (
        select(func.max(GeofenceEvent.id).label("max_id"))
        .where(GeofenceEvent.user_id == user_id)
        .group_by(GeofenceEvent.zone_id)
        .subquery()
    )

    stmt = (
        select(GeofenceEvent)
        .join(subq, GeofenceEvent.id == subq.c.max_id)
    )

    result = await db.execute(stmt)
    last_events = result.scalars().all()
    last_event_map = {e.zone_id: e for e in last_events}

    # Process ENTER and DWELL
    for zone in current_zones:
        last_evt = last_event_map.get(zone.id)

        if not last_evt or last_evt.event_type == 'exit':
            # Entered
            if 'enter' in zone.trigger_on:
                evt = GeofenceEvent(
                    user_id=user_id,
                    zone_id=zone.id,
                    event_type='enter',
                    triggered_at=datetime.utcnow(),
                    metadata_info={"lat": lat, "lon": lon}
                )
                db.add(evt)
                new_events.append(evt)
        elif last_evt.event_type == 'enter' or last_evt.event_type == 'dwell':
            # Still inside (Dwell)
            if 'dwell' in zone.trigger_on and zone.dwell_seconds:
                # Check if dwell time exceeded and we haven't triggered dwell yet (or logic to trigger periodically?)
                # We trigger dwell ONLY if the last event was 'enter'. If it was 'dwell', we already triggered it.
                # Or maybe we trigger it again? Usually "dwell" is once per session.
                if last_evt.event_type == 'enter':
                    elapsed = (datetime.utcnow() - last_evt.triggered_at).total_seconds()
                    if elapsed >= zone.dwell_seconds:
                        evt = GeofenceEvent(
                            user_id=user_id,
                            zone_id=zone.id,
                            event_type='dwell',
                            triggered_at=datetime.utcnow(),
                            metadata_info={"lat": lat, "lon": lon, "dwell_time": elapsed}
                        )
                        db.add(evt)
                        new_events.append(evt)

    # Process EXIT
    # Check zones where user WAS inside (last event = enter/dwell) but is NOT in current_zones
    for zone_id, last_evt in last_event_map.items():
        if zone_id not in current_zone_ids:
            if last_evt.event_type in ['enter', 'dwell']:
                # User has left this zone
                # We need to fetch the zone object to check trigger_on
                # Optimisation: We could have fetched it earlier, but let's just query or assume we trigger.
                # Ideally we check zone.trigger_on.
                # Let's fetch the zone.
                zone_stmt = select(GeofenceZone).where(GeofenceZone.id == zone_id)
                z_res = await db.execute(zone_stmt)
                zone = z_res.scalar_one_or_none()

                if zone and 'exit' in zone.trigger_on:
                    evt = GeofenceEvent(
                        user_id=user_id,
                        zone_id=zone_id,
                        event_type='exit',
                        triggered_at=datetime.utcnow(),
                        metadata_info={"lat": lat, "lon": lon}
                    )
                    db.add(evt)
                    new_events.append(evt)

    # Do not commit here, let the caller handle transaction scope
    return new_events

async def find_points_of_interest(db: AsyncSession, lat: float, lon: float, radius_m: float, categories: List[str]) -> List[POI]:
    """
    Find POIs nearby. Currently returns GeofenceZones as POIs.
    """
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)

    # Search GeofenceZones within radius
    # Using simple ST_DWithin with Geography cast
    stmt = select(GeofenceZone).where(
        func.ST_DWithin(
            func.CAST(GeofenceZone.geometry, Geography),
            func.CAST(point, Geography),
            radius_m
        )
    )

    result = await db.execute(stmt)
    zones = result.scalars().all()

    pois = []
    for z in zones:
        # We need lat/lon from geometry to populate POI
        # If geometry is Polygon, we take centroid.
        # If Point, we take coords.
        # We can use ST_AsGeoJSON or similar, or just ST_X/ST_Y on Centroid
        centroid_stmt = select(
            func.ST_X(func.ST_Centroid(func.ST_GeometryFromText(func.ST_AsText(z.geometry)))),
            func.ST_Y(func.ST_Centroid(func.ST_GeometryFromText(func.ST_AsText(z.geometry))))
        )
        # That's complicated to execute per row.
        # Better to modify the main query to return centroid coords.
        # But for now, we have the object.
        # In geoalchemy2, we can access z.geometry (WKBElement).
        # We can use shapely if we want to parse it in python.
        # Given 'shapely' is in requirements, let's use it.
        from geoalchemy2.shape import to_shape

        shape = to_shape(z.geometry)
        centroid = shape.centroid

        poi = POI(
            id=z.id,
            name=z.name,
            latitude=centroid.y,
            longitude=centroid.x,
            category=z.zone_type # Use zone_type as category for now
        )

        if not categories or (poi.category in categories):
            pois.append(poi)

    return pois

async def calculate_dwell_time(db: AsyncSession, user_id: str, zone_id: int) -> int:
    """
    Calculate dwell time in seconds for the current or last session in the zone.
    """
    # Get latest enter
    stmt = select(GeofenceEvent).where(
        GeofenceEvent.user_id == user_id,
        GeofenceEvent.zone_id == zone_id,
        GeofenceEvent.event_type == 'enter'
    ).order_by(GeofenceEvent.triggered_at.desc()).limit(1)

    result = await db.execute(stmt)
    last_enter = result.scalar_one_or_none()

    if not last_enter:
        return 0

    # Get exit after that enter
    stmt = select(GeofenceEvent).where(
        GeofenceEvent.user_id == user_id,
        GeofenceEvent.zone_id == zone_id,
        GeofenceEvent.event_type == 'exit',
        GeofenceEvent.triggered_at > last_enter.triggered_at
    ).order_by(GeofenceEvent.triggered_at.asc()).limit(1)

    result = await db.execute(stmt)
    next_exit = result.scalar_one_or_none()

    if next_exit:
        return int((next_exit.triggered_at - last_enter.triggered_at).total_seconds())
    else:
        # Still inside
        return int((datetime.utcnow() - last_enter.triggered_at).total_seconds())
