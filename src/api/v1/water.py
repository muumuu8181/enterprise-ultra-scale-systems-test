from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from src.database import get_db
from src.models.water_models import TreatmentPlant, WaterQualitySample, ChemicalDosing, PlantStatus
from src.schemas.water_schemas import (
    TreatmentPlantResponse,
    WaterQualitySampleResponse,
    ChemicalDosingResponse,
    ChemicalDosingCreate,
    DashboardResponse
)

router = APIRouter(prefix="/water", tags=["water"])

@router.get("/plants", response_model=List[TreatmentPlantResponse])
async def get_plants(
    status: Optional[PlantStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(TreatmentPlant)
    if status:
        query = query.where(TreatmentPlant.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/plants/{id}/dashboard", response_model=DashboardResponse)
async def get_plant_dashboard(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    plant_result = await db.execute(select(TreatmentPlant).where(TreatmentPlant.id == id))
    plant = plant_result.scalar_one_or_none()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    # Get latest quality sample
    quality_result = await db.execute(
        select(WaterQualitySample)
        .where(WaterQualitySample.plant_id == id)
        .order_by(desc(WaterQualitySample.sampled_at))
        .limit(1)
    )
    latest_quality = quality_result.scalar_one_or_none()

    # Get latest dosing
    dosing_result = await db.execute(
        select(ChemicalDosing)
        .where(ChemicalDosing.plant_id == id)
        .order_by(desc(ChemicalDosing.timestamp))
        .limit(1)
    )
    latest_dosing = dosing_result.scalar_one_or_none()

    return {
        "plant": plant,
        "latest_quality": latest_quality,
        "latest_dosing": latest_dosing,
        "status": plant.status
    }

@router.get("/quality/{plant_id}/latest", response_model=WaterQualitySampleResponse)
async def get_latest_quality(
    plant_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WaterQualitySample)
        .where(WaterQualitySample.plant_id == plant_id)
        .order_by(desc(WaterQualitySample.sampled_at))
        .limit(1)
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="No samples found for this plant")
    return sample

@router.get("/quality/{plant_id}/trend")
async def get_quality_trend(
    plant_id: int,
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(WaterQualitySample)
        .where(WaterQualitySample.plant_id == plant_id)
        .where(WaterQualitySample.sampled_at >= start_date)
        .order_by(WaterQualitySample.sampled_at)
    )
    return result.scalars().all()

@router.post("/dosing/adjust", response_model=ChemicalDosingResponse)
async def adjust_dosing(
    dosing: ChemicalDosingCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify plant exists
    plant_result = await db.execute(select(TreatmentPlant).where(TreatmentPlant.id == dosing.plant_id))
    if not plant_result.scalar_one_or_none():
         raise HTTPException(status_code=404, detail="Plant not found")

    new_dosing = ChemicalDosing(**dosing.model_dump())
    db.add(new_dosing)
    await db.commit()
    await db.refresh(new_dosing)
    return new_dosing

@router.get("/dosing/{plant_id}/history", response_model=List[ChemicalDosingResponse])
async def get_dosing_history(
    plant_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChemicalDosing)
        .where(ChemicalDosing.plant_id == plant_id)
        .order_by(desc(ChemicalDosing.timestamp))
    )
    return result.scalars().all()

@router.get("/compliance/report")
async def get_compliance_report(
    period: str = Query("30d", pattern="^[0-9]+[dmy]$"),
    db: AsyncSession = Depends(get_db)
):
    days = 30
    if period.endswith('d'):
        days = int(period[:-1])
    elif period.endswith('m'):
        days = int(period[:-1]) * 30
    elif period.endswith('y'):
        days = int(period[:-1]) * 365

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(WaterQualitySample)
        .where(WaterQualitySample.sampled_at >= start_date)
    )
    samples = result.scalars().all()

    total = len(samples)
    compliant_count = sum(1 for s in samples if s.compliant)

    return {
        "period": period,
        "total_samples": total,
        "compliant_samples": compliant_count,
        "compliance_rate": (compliant_count / total * 100) if total > 0 else 0
    }

@router.get("/alerts/active")
async def get_active_alerts(
    db: AsyncSession = Depends(get_db)
):
    # Find plants with issues or non-compliant samples recently
    # Logic: non-compliant samples in last 24h
    start_date = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await db.execute(
        select(WaterQualitySample)
        .where(WaterQualitySample.compliant == False)
        .where(WaterQualitySample.sampled_at >= start_date)
    )
    alerts = result.scalars().all()

    return [
        {"plant_id": a.plant_id, "issue": "Non-compliant sample", "sample_id": a.id, "timestamp": a.sampled_at}
        for a in alerts
    ]
