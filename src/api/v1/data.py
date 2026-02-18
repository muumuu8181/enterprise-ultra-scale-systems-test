from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from pydantic import BaseModel
from src.services.edge_inference import push_model_to_device, aggregate_edge_data, sync_data_to_cloud, DeployResult, SyncResult

router = APIRouter()

# --- Pydantic Models ---

class StreamConfig(BaseModel):
    device_id: str
    stream_type: str  # video, sensor, log
    ingestion_rate: float
    processing_mode: str  # local, cloud, hybrid

class DataPolicyConfig(BaseModel):
    device_id: str
    retention_days: int
    compression_ratio: float
    sync_to_cloud_pct: float
    privacy_filter_rules: Dict[str, Any]

class ModelPushRequest(BaseModel):
    model_id: str
    device_ids: List[str]

# --- Endpoints ---

@router.post("/streams/configure")
async def configure_stream(config: StreamConfig):
    """
    Configures a data stream on an edge device.
    """
    # In a real app, this would validate and save to DB
    return {"status": "success", "message": f"Stream configured for device {config.device_id}", "config": config}

@router.get("/streams/{stream_id}/stats")
async def get_stream_stats(stream_id: int):
    """
    Retrieves statistics for a specific stream.
    """
    return {
        "stream_id": stream_id,
        "uptime_seconds": 3600,
        "throughput_mbps": 12.5,
        "packet_loss_rate": 0.01
    }

@router.get("/devices/{device_id}/local-storage-usage")
async def get_storage_usage(device_id: str):
    """
    Checks local storage usage on an edge device.
    """
    return {
        "device_id": device_id,
        "total_capacity_gb": 64,
        "used_gb": 42.5,
        "available_gb": 21.5,
        "usage_percent": 66.4
    }

@router.post("/data-policies/apply")
async def apply_data_policy(policy: DataPolicyConfig):
    """
    Applies a data retention and sync policy to a device.
    """
    return {"status": "applied", "policy_id": 123, "device_id": policy.device_id}

@router.post("/inference/models/push", response_model=List[DeployResult])
async def push_model(request: ModelPushRequest):
    """
    Pushes an ML model to multiple edge devices.
    """
    return await push_model_to_device(request.model_id, request.device_ids)

@router.get("/inference/results")
async def get_inference_results(device_ids: List[str] = Query(...), metric: str = "latency"):
    """
    Retrieves aggregated inference results from edge devices.
    """
    return await aggregate_edge_data(device_ids, metric)
