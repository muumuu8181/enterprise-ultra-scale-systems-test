from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.services.feature_service import compute_feature, serve_online, detect_feature_drift, DriftReport
from src.models.featurestore_models import EntityType, StorageType, FeatureDType
import datetime

# Pydantic models for request/response
class FeatureGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    entity_type: EntityType
    storage_type: StorageType
    tags: Dict[str, Any] = {}

class FeatureGroupResponse(FeatureGroupCreate):
    id: int

class FeatureCreate(BaseModel):
    group_id: int
    name: str
    dtype: FeatureDType
    transformation_logic: Optional[str] = None
    version: str = "v1"
    lineage: Dict[str, Any] = {}

class FeatureResponse(FeatureCreate):
    id: int

class FeatureViewCreate(BaseModel):
    features: List[str]
    source_query: str
    freshness_minutes: int

class FeatureViewResponse(FeatureViewCreate):
    id: int
    materialized_at: Optional[datetime.datetime] = None

class MaterializeRequest(BaseModel):
    feature_view_id: int

router = APIRouter()

# Mock DB for demo purposes
feature_groups_db = []
features_db = []
feature_views_db = []

@router.post("/feature-groups", response_model=FeatureGroupResponse)
async def create_feature_group(group: FeatureGroupCreate):
    new_group = group.model_dump()
    new_group['id'] = len(feature_groups_db) + 1
    feature_groups_db.append(new_group)
    return new_group

@router.get("/feature-groups/{group_id}/features", response_model=List[FeatureResponse])
async def get_features_in_group(group_id: int):
    # Filter features by group_id
    group_features = [f for f in features_db if f['group_id'] == group_id]
    return group_features

@router.post("/features/register", response_model=FeatureResponse)
async def register_feature(feature: FeatureCreate):
    new_feature = feature.model_dump()
    new_feature['id'] = len(features_db) + 1
    features_db.append(new_feature)
    return new_feature

@router.get("/features/{feature_id}/statistics", response_model=DriftReport)
async def get_feature_statistics(feature_id: int):
    # This calls the service
    report = await detect_feature_drift(feature_id)
    return report

@router.post("/feature-views/materialize", response_model=Dict[str, str])
async def materialize_feature_view(request: MaterializeRequest):
    # Find the view
    view = next((v for v in feature_views_db if v['id'] == request.feature_view_id), None)
    if not view:
        raise HTTPException(status_code=404, detail="Feature view not found")

    # Simulate update
    view['materialized_at'] = datetime.datetime.now()
    return {"status": "materialization_started", "job_id": "job-123"}

@router.get("/feature-views/{view_id}/data")
async def get_feature_view_data(view_id: int, entity_id: str):
    # In a real app we'd fetch the feature definition from view_id
    # Here we mock it by getting random features

    view = next((v for v in feature_views_db if v['id'] == view_id), None)
    if not view:
        raise HTTPException(status_code=404, detail="Feature view not found")

    # Call service
    feature_names = view['features']
    if isinstance(feature_names, str): # Handle JSON string if needed, but pydantic handles lists
         feature_names = [feature_names]

    data = await serve_online(entity_id, feature_names)
    return data

# Endpoint to create views (helper for demo/testing, not strictly requested but needed)
@router.post("/feature-views", response_model=FeatureViewResponse)
async def create_feature_view(view: FeatureViewCreate):
    new_view = view.model_dump()
    new_view['id'] = len(feature_views_db) + 1
    new_view['materialized_at'] = None
    feature_views_db.append(new_view)
    return new_view
