from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date, datetime

from src.database import get_db
from src.models.ground_ops import Turnaround, BaggageCarousel, GroundCrew, TurnaroundStatus, CarouselStatus
from src.services.turnaround_service import monitor_turnaround
from src.schemas.ground_schemas import GroundCrewSchema

router = APIRouter()

@router.get("/turnarounds/{flight_id}/status", response_model=TurnaroundStatus)
async def get_turnaround_status(flight_id: str, db: AsyncSession = Depends(get_db)):
    # In a real app, we might query DB first, then fall back to service or use service to update DB
    # For now, we use the service monitor as requested
    return await monitor_turnaround(flight_id)

@router.post("/turnarounds/{id}/update-step")
async def update_turnaround_step(id: int, step_name: str = Body(...), status: str = Body(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Turnaround).where(Turnaround.id == id))
    turnaround = result.scalar_one_or_none()
    if not turnaround:
        raise HTTPException(status_code=404, detail="Turnaround not found")

    # Ensure steps_completed is a list
    steps = list(turnaround.steps_completed) if turnaround.steps_completed else []
    steps.append({"step": step_name, "status": status, "timestamp": datetime.now().isoformat()})
    turnaround.steps_completed = steps

    # Also update main status if needed, simplified logic
    if status == "completed":
        turnaround.status = TurnaroundStatus.in_progress

    await db.commit()
    return {"message": "Step updated", "steps": steps}

@router.get("/baggage/carousels/{id}/status", response_model=CarouselStatus)
async def get_carousel_status(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BaggageCarousel).where(BaggageCarousel.id == id))
    carousel = result.scalar_one_or_none()
    if not carousel:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return carousel.status

@router.post("/baggage/carousels/{id}/activate")
async def activate_carousel(id: int, flight_id: str = Body(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BaggageCarousel).where(BaggageCarousel.id == id))
    carousel = result.scalar_one_or_none()
    if not carousel:
        raise HTTPException(status_code=404, detail="Carousel not found")

    carousel.status = CarouselStatus.running
    carousel.assigned_flight_id = flight_id
    await db.commit()
    return {"message": "Carousel activated", "status": carousel.status}

@router.get("/ground-crew/assignments", response_model=List[GroundCrewSchema])
async def get_crew_assignments(shift: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(GroundCrew)
    if shift:
        query = query.where(GroundCrew.shift == shift)
    result = await db.execute(query)
    crews = result.scalars().all()
    return crews

@router.post("/ground-crew/dispatch")
async def dispatch_crew(crew_id: int = Body(...), flight_id: str = Body(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GroundCrew).where(GroundCrew.id == crew_id))
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")

    crew.assigned_flight_id = flight_id
    await db.commit()
    return {"message": "Crew dispatched", "assigned_flight_id": flight_id}
