from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.models.satellite_models import ImageScene, ChangeDetection
from src.services.imagery_service import ImageryService, ProcessingResult, LandCoverMap

router = APIRouter()

def get_imagery_service():
    return ImageryService()

class SearchRequest(BaseModel):
    bbox_geojson: dict
    start_date: datetime
    end_date: datetime
    max_cloud_cover_pct: float

class OrderRequest(BaseModel):
    satellite_id: str
    target_date: datetime
    bbox_geojson: dict

@router.post("/imagery/search", response_model=List[ImageScene])
async def search_imagery(
    request: SearchRequest,
    service: ImageryService = Depends(get_imagery_service)
):
    # Placeholder: return an empty list or mock data
    return []

@router.get("/imagery/{id}/thumbnail")
async def get_thumbnail(
    id: str,
    service: ImageryService = Depends(get_imagery_service)
):
    # Placeholder: return a file or url
    return {"url": f"https://example.com/thumbnails/{id}.jpg"}

@router.post("/imagery/order")
async def order_imagery(
    request: OrderRequest,
    service: ImageryService = Depends(get_imagery_service)
):
    # Placeholder: return order confirmation
    return {"order_id": "ord_123", "status": "submitted"}

@router.get("/imagery/{id}/download")
async def download_imagery(
    id: str,
    service: ImageryService = Depends(get_imagery_service)
):
    # Placeholder: return download url
    return {"download_url": f"https://example.com/downloads/{id}.tif"}

@router.get("/change-detection/run")
async def run_change_detection(
    scene1_id: str,
    scene2_id: str,
    service: ImageryService = Depends(get_imagery_service)
):
    # In a real app this might trigger a background task and return a task ID
    # But here we can just call the service for simplicity or mock async behavior
    # The prompt says "async", implying triggering a process.
    return {"task_id": "task_456", "status": "processing"}

@router.get("/change-detection/{id}/results", response_model=List[ChangeDetection])
async def get_change_detection_results(
    id: str,
    service: ImageryService = Depends(get_imagery_service)
):
    # Typically id here would be the task_id or change detection run id
    # For simplicity, we'll mock returning results based on the id
    return await service.detect_changes("scene_A", "scene_B")
