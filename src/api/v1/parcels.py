from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.session import get_db
from src.services.urban_service import UrbanService
from src.models.urban_models import LandParcel, UrbanZone, DevelopmentProject
from src.schemas.urban_schemas import (
    LandParcelCreate, LandParcelResponse,
    DevelopmentProjectCreate, DevelopmentProjectResponse,
    ImpactReport, OptimizationResult
)
from typing import List, Optional
import json
import uuid
from shapely.geometry import shape

router = APIRouter()

def get_service(db: AsyncSession = Depends(get_db)):
    return UrbanService(db)

@router.post("/parcels/import")
async def import_parcels(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    count = 0
    if "features" in data:
        for feature in data["features"]:
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            if not geom:
                continue

            # Create LandParcel
            # Convert geometry to WKB hex string for insertion
            wkb_geometry = shape(geom).wkb_hex

            parcel = LandParcel(
                parcel_id=props.get("parcel_id", str(uuid.uuid4())),
                zoning_code=props.get("zoning_code", "UNKNOWN"),
                area_sqm=props.get("area_sqm", 0.0),
                current_use=props.get("current_use", "VACANT"),
                allowed_uses=props.get("allowed_uses", []),
                geometry=wkb_geometry
            )
            db.add(parcel)
            count += 1

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"Imported {count} parcels"}

@router.get("/parcels/search", response_model=List[LandParcelResponse])
async def search_parcels(zone: Optional[str] = None, use: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(LandParcel)
    if zone:
        query = query.where(LandParcel.zoning_code == zone)
    if use:
        query = query.where(LandParcel.current_use == use)

    result = await db.execute(query)
    parcels = result.scalars().all()
    return list(parcels)

@router.get("/parcels/{id}/development-potential")
async def get_development_potential(id: int, db: AsyncSession = Depends(get_db)):
    parcel = await db.get(LandParcel, id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    # Logic to calculate potential
    return {"potential_score": 85, "max_floors": 10, "max_units": 50}

@router.post("/parcels/{id}/zoning-change")
async def change_zoning(id: int, new_zone: str, db: AsyncSession = Depends(get_db)):
    parcel = await db.get(LandParcel, id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    parcel.zoning_code = new_zone
    await db.commit()
    return {"message": "Zoning updated", "new_zone": new_zone}

@router.get("/zones/{id}/statistics")
async def get_zone_statistics(id: int, db: AsyncSession = Depends(get_db)):
    zone = await db.get(UrbanZone, id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {
        "population_density": zone.population_density,
        "avg_income": zone.avg_income,
        "infrastructure_score": zone.infrastructure_score
    }

@router.post("/zones/impact-analysis", response_model=ImpactReport)
async def analyze_impact(project: DevelopmentProjectCreate, service: UrbanService = Depends(get_service)):
    # Create temporary project model for calculation (not saving to DB yet)
    db_project = DevelopmentProject(**project.model_dump())
    db_project.id = 0 # Dummy ID
    return await service.calculate_development_impact(db_project)
