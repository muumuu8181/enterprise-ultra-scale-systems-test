from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.pgx_service import compute_pgx_profile, run_gwas, GWASResult
from src.models.clinical_genomics import PharmacogenomicProfile, PopulationStudy, PanelDesign
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any

router = APIRouter()

# Pydantic schemas
class PanelDesignCreate(BaseModel):
    name: str
    genes: List[str]
    disease_indication: str
    coverage_target_pct: float
    bait_set_uri: str

class PanelDesignResponse(BaseModel):
    id: int
    name: str
    genes: List[str]
    disease_indication: str
    coverage_target_pct: float
    bait_set_uri: str

    model_config = ConfigDict(from_attributes=True)

class PharmacogenomicProfileResponse(BaseModel):
    id: int
    patient_id: str
    cyp2d6_phenotype: str
    cyp2c19_phenotype: str
    drug_recommendations: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)

class GWASRequest(BaseModel):
    study_id: int

@router.get("/patients/{id}/pgx-profile", response_model=PharmacogenomicProfileResponse)
async def get_pgx_profile(id: str, db: AsyncSession = Depends(get_db)):
    profile = await compute_pgx_profile(id, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/patients/{id}/drug-interactions")
async def get_drug_interactions(id: str, db: AsyncSession = Depends(get_db)):
    profile = await compute_pgx_profile(id, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Mock interactions based on profile
    return {"interactions": ["Avoid codeine due to CYP2D6 poor metabolizer status"]}

@router.post("/population-studies/gwas", response_model=GWASResult)
async def execute_gwas(request: GWASRequest, db: AsyncSession = Depends(get_db)):
    result = await run_gwas(request.study_id, db)
    return result

@router.get("/population-studies/{id}/manhattan-plot")
async def get_manhattan_plot(id: int):
    # Return a mock URL or image data
    return {"url": f"https://minio.example.com/plots/{id}/manhattan.png"}

@router.post("/panels/design", response_model=PanelDesignResponse)
async def create_panel_design(design: PanelDesignCreate, db: AsyncSession = Depends(get_db)):
    new_design = PanelDesign(
        name=design.name,
        genes=design.genes,
        disease_indication=design.disease_indication,
        coverage_target_pct=design.coverage_target_pct,
        bait_set_uri=design.bait_set_uri
    )
    db.add(new_design)
    await db.commit()
    await db.refresh(new_design)
    return new_design

@router.get("/panels/{id}/performance-metrics")
async def get_panel_metrics(id: int, db: AsyncSession = Depends(get_db)):
    # Mock metrics
    return {
        "panel_id": id,
        "mean_coverage": "100x",
        "uniformity": "98%",
        "on_target_rate": "95%"
    }
