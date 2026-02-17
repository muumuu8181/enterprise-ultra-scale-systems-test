from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from src.database import get_db
from src.models.cctv_models import CCTVCamera, CCTVAnalytics, CCTVIncident
from src.services.video_analytics import VideoAnalyticsService
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/cctv", tags=["cctv"])
analytics_service = VideoAnalyticsService()

# Schemas
class CameraCreate(BaseModel):
    camera_id: str
    latitude: float
    longitude: float
    status: str = "active"
    stream_url: Optional[str] = None
    enabled_analytics: Optional[Dict[str, Any]] = {}

class CameraResponse(BaseModel):
    id: int
    camera_id: str
    status: str
    stream_url: Optional[str]
    enabled_analytics: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)

class AnalyticsStats(BaseModel):
    id: int
    camera_id: int
    timestamp: datetime
    crowd_density: float
    vehicle_count: int
    anomaly_detected: bool
    model_config = ConfigDict(from_attributes=True)

class IncidentCreate(BaseModel):
    camera_id: int
    type: str
    screenshot_url: Optional[str] = None

class IncidentResponse(BaseModel):
    id: int
    camera_id: int
    incident_type: str
    screenshot_url: Optional[str]
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class AnalyticsEnableRequest(BaseModel):
    features: Dict[str, bool] # e.g. {"face_detection": true, "crowd_density": true}

# Endpoints

@router.get("/cameras", response_model=List[CameraResponse])
async def list_cameras(db: AsyncSession = Depends(get_db)):
    """
    カメラ一覧取得
    """
    result = await db.execute(select(CCTVCamera))
    return result.scalars().all()

@router.post("/cameras", response_model=CameraResponse)
async def create_camera(camera: CameraCreate, db: AsyncSession = Depends(get_db)):
    """
    カメラ登録 (テスト用)
    """
    point = f"POINT({camera.longitude} {camera.latitude})"
    db_camera = CCTVCamera(
        camera_id=camera.camera_id,
        location=WKTElement(point, srid=4326),
        status=camera.status,
        stream_url=camera.stream_url,
        enabled_analytics=camera.enabled_analytics
    )
    db.add(db_camera)
    try:
        await db.commit()
        await db.refresh(db_camera)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_camera

@router.get("/cameras/{id}/stream")
async def get_stream_url(id: int, db: AsyncSession = Depends(get_db)):
    """
    ストリームURL取得
    """
    camera = await db.get(CCTVCamera, id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"stream_url": camera.stream_url}

@router.post("/cameras/{id}/analytics/enable")
async def enable_analytics(id: int, request: AnalyticsEnableRequest, db: AsyncSession = Depends(get_db)):
    """
    解析機能の有効化
    """
    camera = await db.get(CCTVCamera, id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    current_analytics = dict(camera.enabled_analytics) if camera.enabled_analytics else {}
    current_analytics.update(request.features)

    # SQLAlchemy might not track mutation of JSON dict, so reassign
    camera.enabled_analytics = current_analytics

    await db.commit()
    return {"message": "Analytics updated", "enabled_analytics": camera.enabled_analytics}

@router.get("/analytics/{camera_id}/stats", response_model=List[AnalyticsStats])
async def get_analytics_stats(camera_id: int, db: AsyncSession = Depends(get_db)):
    """
    解析結果取得
    """
    query = select(CCTVAnalytics).where(CCTVAnalytics.camera_id == camera_id).order_by(CCTVAnalytics.timestamp.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/incidents", response_model=IncidentResponse)
async def report_incident(incident: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """
    インシデント記録
    """
    # Verify camera exists
    camera = await db.get(CCTVCamera, incident.camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    db_incident = CCTVIncident(
        camera_id=incident.camera_id,
        incident_type=incident.type,
        screenshot_url=incident.screenshot_url
    )
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    return db_incident
