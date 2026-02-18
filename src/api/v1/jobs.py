from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from src.models.compute_models import ComputeJob, JobType, JobStatus
from src.services.scheduler import schedule_job

router = APIRouter(prefix="/jobs", tags=["jobs"])

# In-memory storage for demo purposes
jobs_db = {}

class JobSubmitRequest(BaseModel):
    user_id: str
    job_type: JobType
    priority: int = 0
    walltime_sec: Optional[int] = 3600
    nodes_requested: int = 1
    gpus_requested: int = 0

class JobResponse(BaseModel):
    id: int
    user_id: str
    job_type: str
    status: str
    priority: int
    created_at: datetime

@router.post("/submit", response_model=JobResponse)
async def submit_job(job: JobSubmitRequest):
    job_id = len(jobs_db) + 1
    new_job = ComputeJob(
        id=job_id,
        user_id=job.user_id,
        job_type=job.job_type,
        status=JobStatus.PENDING,
        priority=job.priority,
        walltime_sec=job.walltime_sec,
        nodes_requested=job.nodes_requested,
        gpus_requested=job.gpus_requested,
        created_at=datetime.now(timezone.utc)
    )
    jobs_db[job_id] = new_job

    # Schedule logic
    await schedule_job(new_job)

    return JobResponse(
        id=new_job.id,
        user_id=new_job.user_id,
        job_type=new_job.job_type.value,
        status=new_job.status.value,
        priority=new_job.priority,
        created_at=new_job.created_at
    )

@router.get("/{id}/status")
async def get_job_status(id: int = Path(..., title="The ID of the job")):
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs_db[id]
    return {"id": job.id, "status": job.status.value}

@router.get("/{id}/stdout")
async def get_job_stdout(id: int = Path(..., title="The ID of the job")):
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": id, "stdout": "Simulation running...\nStep 1: Done\nStep 2: Processing..."}

@router.get("/{id}/output-files")
async def get_job_output_files(id: int = Path(..., title="The ID of the job")):
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": id, "files": ["results.csv", "plot.png", "metadata.json"]}

@router.post("/{id}/cancel")
async def cancel_job(id: int = Path(..., title="The ID of the job")):
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    jobs_db[id].status = JobStatus.CANCELLED
    return {"id": id, "status": "cancelled"}

@router.get("/queue/position")
async def get_queue_position(job_id: Optional[int] = Query(None)):
    if job_id:
        if job_id not in jobs_db:
             raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job_id, "position": 2}

    return {"queue_depth": len(jobs_db), "estimated_wait_sec": 120}
