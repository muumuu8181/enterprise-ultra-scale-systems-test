from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy import select, desc
from src.database import AsyncSessionLocal
from src.models.vessel_models import Vessel, AISPosition, Port, VesselType
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
import math

class DarkShipAlert(BaseModel):
    vessel_id: int
    gap_start: datetime
    gap_end: datetime
    last_known_location: tuple[float, float]
    severity: str

async def ingest_ais_stream(messages: List[Dict[str, Any]]) -> int:
    """
    Ingests a stream of AIS messages.
    Each message must contain 'mmsi' and AISPosition fields.
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for msg in messages:
            mmsi = msg.get("mmsi")
            if not mmsi:
                continue

            # Find or create vessel
            stmt = select(Vessel).where(Vessel.mmsi == mmsi)
            result = await session.execute(stmt)
            vessel = result.scalar_one_or_none()

            if not vessel:
                v_type_str = msg.get("vessel_type", "other").lower()
                try:
                    v_type = VesselType(v_type_str)
                except ValueError:
                    v_type = VesselType.OTHER

                # Basic vessel creation if not exists
                vessel = Vessel(
                    mmsi=mmsi,
                    vessel_name=msg.get("vessel_name", f"Unknown Vessel {mmsi}"),
                    vessel_type=v_type,
                    flag_country=msg.get("flag_country", "Unknown"),
                    length_m=msg.get("length_m", 0.0),
                    gross_tonnage=msg.get("gross_tonnage", 0),
                    owner_id=msg.get("owner_id", 0)
                )
                session.add(vessel)
                await session.flush() # to get ID

            # Create position
            lat = msg.get("latitude")
            lon = msg.get("longitude")
            if lat is None or lon is None:
                continue

            # Ensure timestamp is offset-aware
            ts = msg.get("timestamp")
            if ts is None:
                ts = datetime.now(timezone.utc)
            elif isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except ValueError:
                    ts = datetime.now(timezone.utc)

            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            position = AISPosition(
                vessel_id=vessel.id,
                timestamp=ts,
                latitude=lat,
                longitude=lon,
                speed_knots=msg.get("speed_knots", 0.0),
                course=msg.get("course", 0.0),
                navigational_status=msg.get("navigational_status", "under way"),
                draught=msg.get("draught", 0.0),
                location=f"POINT({lon} {lat})"
            )
            session.add(position)
            count += 1

        await session.commit()
    return count

async def predict_eta(vessel_id: int, destination_port_id: int) -> Optional[datetime]:
    async with AsyncSessionLocal() as session:
        # Get latest position
        pos_stmt = select(AISPosition).where(AISPosition.vessel_id == vessel_id).order_by(desc(AISPosition.timestamp)).limit(1)
        pos_result = await session.execute(pos_stmt)
        last_pos = pos_result.scalar_one_or_none()

        if not last_pos:
            return None

        # Get port location
        port_stmt = select(Port).where(Port.id == destination_port_id)
        port_result = await session.execute(port_stmt)
        port = port_result.scalar_one_or_none()

        if not port:
            return None

        # Simple distance calculation (Haversine)
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(last_pos.latitude), math.radians(last_pos.longitude)

        # Extract port location
        port_shape = to_shape(port.location)
        lat2, lon2 = math.radians(port_shape.y), math.radians(port_shape.x)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c
        distance_nm = distance_km * 0.539957

        speed = last_pos.speed_knots
        if speed <= 0.1:
            return None # Stationary or too slow to predict

        hours = distance_nm / speed
        eta = last_pos.timestamp + timedelta(hours=hours)
        return eta

async def detect_dark_ship(vessel_id: int) -> Optional[DarkShipAlert]:
    async with AsyncSessionLocal() as session:
        # Get last 24 hours of positions
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = select(AISPosition).where(
            AISPosition.vessel_id == vessel_id,
            AISPosition.timestamp >= cutoff
        ).order_by(AISPosition.timestamp)

        result = await session.execute(stmt)
        positions = result.scalars().all()

        if len(positions) < 2:
            return None

        max_gap = timedelta(0)
        gap_start = None
        gap_end = None
        last_known_loc = None

        for i in range(len(positions) - 1):
            curr = positions[i]
            next_pos = positions[i+1]
            gap = next_pos.timestamp - curr.timestamp

            if gap > max_gap:
                max_gap = gap
                gap_start = curr.timestamp
                gap_end = next_pos.timestamp
                last_known_loc = (curr.latitude, curr.longitude)

        # Threshold: e.g., 2 hours
        if max_gap > timedelta(hours=2):
            return DarkShipAlert(
                vessel_id=vessel_id,
                gap_start=gap_start,
                gap_end=gap_end,
                last_known_location=last_known_loc,
                severity="high" if max_gap > timedelta(hours=6) else "medium"
            )

        return None
