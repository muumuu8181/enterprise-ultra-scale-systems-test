from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from src.models.genomics_models import (
    GenomicSampleResponse,
    GenomicSampleCreate,
    SampleStatus,
    VariantResponse,
    GenomicReport
)
from src.services import variant_service

router = APIRouter()

# Mock storage
SAMPLES_DB = {}
PIPELINES_DB = {}

class PipelineRunRequest(BaseModel):
    sample_id: int

@router.post("/samples/register", response_model=GenomicSampleResponse)
async def register_sample(sample: GenomicSampleCreate):
    sample_id = len(SAMPLES_DB) + 1
    new_sample = GenomicSampleResponse(
        id=sample_id,
        patient_id=sample.patient_id,
        sample_type=sample.sample_type,
        sequencing_type=sample.sequencing_type,
        status=SampleStatus.received
    )
    SAMPLES_DB[sample_id] = new_sample
    return new_sample

@router.get("/samples/{id}/status", response_model=dict)
async def get_sample_status(id: int):
    if id not in SAMPLES_DB:
        raise HTTPException(status_code=404, detail="Sample not found")
    return {"status": SAMPLES_DB[id].status}

@router.get("/samples/{id}/variants", response_model=List[VariantResponse])
async def get_sample_variants(id: int, significance: Optional[str] = None):
    if id not in SAMPLES_DB:
        raise HTTPException(status_code=404, detail="Sample not found")

    variants = await variant_service.annotate_variants(id)

    if significance:
        variants = [v for v in variants if v.clinvar_significance == significance]

    return variants

@router.get("/samples/{id}/report", response_model=GenomicReport)
async def get_sample_report(id: int):
    if id not in SAMPLES_DB:
        raise HTTPException(status_code=404, detail="Sample not found")

    report = await variant_service.generate_clinical_report(id)
    # Ensure the report matches the sample in our mock DB
    report.patient_id = SAMPLES_DB[id].patient_id
    report.status = SAMPLES_DB[id].status
    return report

@router.post("/pipelines/run", response_model=dict)
async def run_pipeline(request: PipelineRunRequest):
    sample_id = request.sample_id
    if sample_id not in SAMPLES_DB:
        raise HTTPException(status_code=404, detail="Sample not found")

    pipeline_id = len(PIPELINES_DB) + 1
    PIPELINES_DB[pipeline_id] = {"status": "running", "sample_id": sample_id}

    # Update sample status
    SAMPLES_DB[sample_id].status = SampleStatus.processing

    return {"pipeline_id": pipeline_id, "status": "started"}

@router.get("/pipelines/{id}/progress", response_model=dict)
async def get_pipeline_progress(id: int):
    if id not in PIPELINES_DB:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return {"id": id, "status": PIPELINES_DB[id]["status"], "progress": "50%"}
