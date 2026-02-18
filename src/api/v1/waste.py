from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from src.database import get_db
from src.models.waste_models import WasteBin, CollectionRoute
from src.services.route_optimizer import optimize_collection_route
from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/waste", tags=["waste"])

# Schemas
class WasteBinResponse(BaseModel):
    id: int
    location: Dict[str, float]
    district: str
    bin_type: str
    capacity_liters: int
    fill_level: float
    last_collected: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('location', mode='before')
    @classmethod
    def serialize_location(cls, v: Any) -> Dict[str, float]:
        # Handle GeoAlchemy2 elements
        if isinstance(v, (WKBElement, WKTElement)) or hasattr(v, "geom_type"):
            shape = to_shape(v)
            return {"lat": shape.y, "lon": shape.x}
        return v

class FillLevelUpdate(BaseModel):
    fill_level: float

class CollectionRouteResponse(BaseModel):
    id: int
    date: datetime
    driver_id: str
    waypoints: List[Dict[str, Any]]
    total_distance_km: float
    estimated_duration_min: float

    model_config = ConfigDict(from_attributes=True)

class OptimizeRequest(BaseModel):
    district: Optional[str] = None
    driver_id: str = "default_driver"

# Endpoints

@router.get("/bins", response_model=List[WasteBinResponse])
async def get_bins(district: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    ゴミ箱一覧を取得
    """
    query = select(WasteBin)
    if district:
        query = query.where(WasteBin.district == district)

    result = await db.execute(query)
    bins = result.scalars().all()
    return bins

@router.put("/bins/{bin_id}/fill-level", response_model=WasteBinResponse)
async def update_fill_level(bin_id: int, update: FillLevelUpdate, db: AsyncSession = Depends(get_db)):
    """
    ゴミ箱の充填率を更新
    """
    bin = await db.get(WasteBin, bin_id)
    if not bin:
        raise HTTPException(status_code=404, detail="Bin not found")

    bin.fill_level = update.fill_level
    await db.commit()
    await db.refresh(bin)
    return bin

@router.post("/collection/optimize", response_model=CollectionRouteResponse)
async def optimize_route(request: OptimizeRequest, db: AsyncSession = Depends(get_db)):
    """
    収集ルートの最適化を実行し、結果を保存
    """
    query = select(WasteBin)
    if request.district:
        query = query.where(WasteBin.district == request.district)

    result = await db.execute(query)
    bins = result.scalars().all()

    if not bins:
        raise HTTPException(status_code=404, detail="No bins found for optimization")

    # 最適化ロジックの実行
    optimized_data = optimize_collection_route(bins)

    # 結果の保存
    route = CollectionRoute(
        date=datetime.utcnow(),
        driver_id=request.driver_id,
        waypoints=optimized_data["waypoints"],
        total_distance_km=optimized_data["total_distance_km"],
        estimated_duration_min=optimized_data["estimated_duration_min"]
    )

    db.add(route)
    await db.commit()
    await db.refresh(route)

    return route

@router.get("/collection/routes", response_model=List[CollectionRouteResponse])
async def get_routes(db: AsyncSession = Depends(get_db)):
    """
    最適化されたルートの一覧を取得
    """
    query = select(CollectionRoute).order_by(CollectionRoute.date.desc())
    result = await db.execute(query)
    routes = result.scalars().all()
    return routes
