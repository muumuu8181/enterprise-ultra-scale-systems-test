from fastapi import APIRouter, Path
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone

router = APIRouter(prefix="/clusters", tags=["clusters"])

class ResourceRequest(BaseModel):
    cluster_id: str
    nodes: int
    duration_sec: int
    project_id: str

class Reservation(BaseModel):
    id: str
    cluster_id: str
    nodes: int
    start_time: datetime
    end_time: datetime
    status: str

@router.get("/{id}/utilization")
async def get_cluster_utilization(id: str = Path(..., title="The ID of the cluster")):
    # Mock implementation
    return {
        "cluster_id": id,
        "cpu_usage_percent": 75.5,
        "gpu_usage_percent": 90.2,
        "memory_usage_gb": 10240,
        "active_jobs": 42
    }

@router.get("/{id}/queue")
async def get_cluster_queue(id: str = Path(..., title="The ID of the cluster")):
    # Mock implementation
    return {
        "cluster_id": id,
        "pending_jobs": 15,
        "running_jobs": 42,
        "average_wait_time_sec": 300
    }

@router.post("/resource-request")
async def request_resources(request: ResourceRequest):
    # Mock implementation
    return {
        "request_id": "req_12345",
        "status": "approved",
        "granted_nodes": request.nodes,
        "valid_until": datetime.now(timezone.utc)
    }

@router.get("/reservations", response_model=List[Reservation])
async def get_reservations():
    # Mock implementation
    return [
        Reservation(
            id="res_001",
            cluster_id="cluster_A",
            nodes=10,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            status="active"
        )
    ]
