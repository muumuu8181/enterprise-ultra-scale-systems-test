from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement

from src.models.workzone_models import WorkZone
from src.services.workzone_broadcaster import WorkZoneBroadcaster

router = APIRouter(prefix="/workzone", tags=["workzone"])

# Dependency Injection (placeholder)
async def get_db():
    yield None

broadcaster = WorkZoneBroadcaster()

@router.post("/zones")
async def create_work_zone(
    location: str = Body(..., description="WKT Polygon string"),
    contractor: str = Body(...),
    speed_limit: float = Body(...),
    closed_lanes: dict = Body(..., alias="lane_closures"),
    start_date: datetime = Body(...),
    end_date: datetime = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new Work Zone.
    """
    if db:
        zone = WorkZone(
            location=WKTElement(location, srid=4326),
            contractor=contractor,
            speed_limit=speed_limit,
            closed_lanes=closed_lanes,
            start_date=start_date,
            end_date=end_date,
            status="active"
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)

        # Initial broadcast
        denm = broadcaster.generate_denm_message(zone)
        await broadcaster.broadcast_to_rsus(denm)
        await broadcaster.update_hd_map(zone)

        return {"status": "created", "id": zone.id}

    # Mock behavior if no DB
    return {"status": "created", "id": 1, "mock": True}

@router.get("/zones/active")
async def get_active_zones(
    bounds: Optional[str] = Query(None, description="Bounding box WKT or similar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active Work Zones.
    """
    if not db:
        return []

    query = select(WorkZone).where(WorkZone.status == "active")

    if bounds:
        # Assuming bounds is a WKT polygon for the search area
        # Use ST_Intersects to find zones overlapping with the bounds
        bounds_geom = WKTElement(bounds, srid=4326)
        query = query.where(func.ST_Intersects(WorkZone.location, bounds_geom))

    result = await db.execute(query)
    return result.scalars().all()

@router.put("/zones/{id}/status")
async def update_work_zone_status(
    id: int,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the status of a Work Zone.
    """
    if not db:
        return {"status": "updated", "id": id, "new_status": status, "mock": True}

    query = select(WorkZone).where(WorkZone.id == id)
    result = await db.execute(query)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(status_code=404, detail="WorkZone not found")

    zone.status = status
    await db.commit()

    if status == "completed":
        await broadcaster.update_hd_map(zone)

    return {"status": "updated", "id": id, "new_status": status}

@router.post("/zones/{id}/broadcast")
async def broadcast_work_zone(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger V2X broadcast for a Work Zone.
    """
    if not db:
        # Mock logic
        zone = WorkZone(
            id=id,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            speed_limit=30.0,
            closed_lanes={},
            location="POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
        )
        denm = broadcaster.generate_denm_message(zone)
        await broadcaster.broadcast_to_rsus(denm)
        return {"status": "broadcasted", "id": id, "mock": True}

    query = select(WorkZone).where(WorkZone.id == id)
    result = await db.execute(query)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(status_code=404, detail="WorkZone not found")

    denm = broadcaster.generate_denm_message(zone)
    await broadcaster.broadcast_to_rsus(denm)

    return {"status": "broadcasted", "id": id}
