from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List
from src.models.compute_models import ComputeJob

class NodeAssignment(BaseModel):
    job_id: int
    node_ids: List[int]
    scheduled_at: datetime
    status: str

class CheckpointResult(BaseModel):
    job_id: int
    checkpoint_path: str
    timestamp: datetime
    success: bool

async def schedule_job(job: ComputeJob) -> NodeAssignment:
    # Mock implementation
    # Handle case where job.nodes_requested might be None or 0
    requested = job.nodes_requested if job.nodes_requested else 1
    return NodeAssignment(
        job_id=job.id,
        node_ids=list(range(101, 101 + requested)),
        scheduled_at=datetime.now(timezone.utc),
        status="scheduled"
    )

async def checkpoint_job(job_id: int) -> CheckpointResult:
    # Mock implementation
    return CheckpointResult(
        job_id=job_id,
        checkpoint_path=f"/checkpoints/job_{job_id}/ckpt_1.pth",
        timestamp=datetime.now(timezone.utc),
        success=True
    )
