from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date, timedelta
from src.database import get_db
from src.models.agri_models import Field, SensorNode, CropPrescription, PrescriptionStatus
from src.schemas.agri_schemas import (
    FieldResponse,
    SensorNodeResponse,
    CropPrescriptionCreate,
    CropPrescriptionResponse,
    HealthDashboard,
    YieldPrediction,
    WeatherForecast
)
from geoalchemy2.shape import to_shape
from shapely.geometry import shape, mapping

router = APIRouter()

def wkt_to_geojson(wkt_element) -> dict:
    if wkt_element is None:
        return {}
    return mapping(to_shape(wkt_element))

@router.get("/fields", response_model=List[FieldResponse])
async def get_fields(
    farm: Optional[str] = None,
    crop: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Field)
    if farm:
        query = query.where(Field.farm_id == farm)
    if crop:
        query = query.where(Field.crop_type == crop)
    result = await db.execute(query)
    fields = result.scalars().all()

    return [
        FieldResponse(
            id=f.id,
            farm_id=f.farm_id,
            name=f.name,
            location=wkt_to_geojson(f.location),
            area_hectares=f.area_hectares,
            crop_type=f.crop_type,
            soil_type=f.soil_type,
            irrigation_type=f.irrigation_type,
            planting_date=f.planting_date,
            expected_harvest=f.expected_harvest
        ) for f in fields
    ]

@router.get("/fields/{id}/health-dashboard", response_model=HealthDashboard)
async def get_health_dashboard(id: int, db: AsyncSession = Depends(get_db)):
    return HealthDashboard(field_id=id, health_score=85.5, alerts=["Low moisture in sector 3"])

@router.get("/sensors/{field_id}/live", response_model=List[SensorNodeResponse])
async def get_sensors_live(field_id: int, db: AsyncSession = Depends(get_db)):
    query = select(SensorNode).where(SensorNode.field_id == field_id)
    result = await db.execute(query)
    sensors = result.scalars().all()

    return [
        SensorNodeResponse(
            id=s.id,
            field_id=s.field_id,
            sensor_type=s.sensor_type,
            location=wkt_to_geojson(s.location),
            battery_pct=s.battery_pct,
            last_reading_at=s.last_reading_at,
            status=s.status
        ) for s in sensors
    ]

@router.get("/sensors/{field_id}/historical")
async def get_sensors_historical(
    field_id: int,
    metric: str = Query(..., description="Metric to query (e.g., temperature)"),
    days: int = Query(7, description="Number of days to look back")
):
    return {"field_id": field_id, "metric": metric, "days": days, "data": []}

@router.post("/prescriptions/create", response_model=CropPrescriptionResponse)
async def create_prescription(prescription: CropPrescriptionCreate, db: AsyncSession = Depends(get_db)):
    db_prescription = CropPrescription(**prescription.model_dump())
    db.add(db_prescription)
    await db.commit()
    await db.refresh(db_prescription)
    return db_prescription

@router.get("/prescriptions/{field_id}/upcoming", response_model=List[CropPrescriptionResponse])
async def get_upcoming_prescriptions(field_id: int, db: AsyncSession = Depends(get_db)):
    query = select(CropPrescription).where(
        CropPrescription.field_id == field_id,
        CropPrescription.status == PrescriptionStatus.planned,
        CropPrescription.scheduled_date >= date.today()
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/analytics/yield-prediction", response_model=YieldPrediction)
async def get_yield_prediction(field_id: int = Query(...)):
    return YieldPrediction(field_id=field_id, predicted_yield=12000.5, confidence=0.85)

@router.get("/weather/{field_id}/7day", response_model=List[WeatherForecast])
async def get_weather_forecast(field_id: int):
    return [
        WeatherForecast(
            field_id=field_id,
            date=date.today() + timedelta(days=i),
            temperature=25.0 + i,
            precipitation=0.0,
            humidity=60.0
        ) for i in range(7)
    ]

@router.post("/irrigation/{field_id}/toggle")
async def toggle_irrigation(field_id: int, status: bool = Query(..., description="True for ON, False for OFF")):
    return {"field_id": field_id, "irrigation_status": "ON" if status else "OFF"}
