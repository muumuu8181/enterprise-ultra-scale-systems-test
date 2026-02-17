from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json

from src.models.training_models import Base, TrainingDataset, ExperimentRun, ModelLineage
from src.services.training_service import create_training_dataset

# Database setup (minimal for this module)
SQLALCHEMY_DATABASE_URL = "sqlite:///./ml_featurestore.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

class CreateTrainingDatasetRequest(BaseModel):
    feature_view_id: str
    label_query: str
    start_date: datetime
    end_date: datetime

class CreateExperimentRunRequest(BaseModel):
    experiment_id: str
    feature_dataset_id: int
    hyperparams: Dict[str, Any]
    metrics: Dict[str, Any]
    artifacts: Dict[str, Any]
    status: str

class BackfillRequest(BaseModel):
    feature_view_id: str
    start_date: datetime
    end_date: datetime

@router.post("/training-datasets/create")
async def create_dataset(request: CreateTrainingDatasetRequest, db: Session = Depends(get_db)):
    try:
        # We pass the individual fields as expected by the service function
        dataset = await create_training_dataset(
            db,
            request.feature_view_id,
            request.label_query,
            request.start_date,
            request.end_date
        )
        return dataset
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-datasets/{id}/download")
def download_dataset(id: int, db: Session = Depends(get_db)):
    dataset = db.query(TrainingDataset).filter(TrainingDataset.id == id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # In a real app, this would stream the file from S3 or return a presigned URL
    return {"url": dataset.snapshot_path}

@router.post("/experiments/runs")
def create_experiment_run(request: CreateExperimentRunRequest, db: Session = Depends(get_db)):
    run = ExperimentRun(
        experiment_id=request.experiment_id,
        feature_dataset_id=request.feature_dataset_id,
        hyperparams=request.hyperparams,
        metrics=request.metrics,
        artifacts=request.artifacts,
        status=request.status
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

@router.get("/experiments/{id}/best-run")
def get_best_run(id: str, db: Session = Depends(get_db)):
    # Mock logic: retrieve run with best metric.
    # For this exercise, we return the latest run for the experiment_id
    run = db.query(ExperimentRun).filter(ExperimentRun.experiment_id == id).order_by(ExperimentRun.id.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return run

@router.get("/models/{id}/lineage")
def get_model_lineage(id: str, db: Session = Depends(get_db)):
    # Mock logic: return lineage for model_id
    lineage = db.query(ModelLineage).filter(ModelLineage.model_id == id).first()
    if not lineage:
        # Return empty or mock lineage
        return {"model_id": id, "lineage": "not found"}
    return lineage

@router.post("/features/backfill")
def backfill_features(request: BackfillRequest, background_tasks: BackgroundTasks):
    # Mock backfill logic
    background_tasks.add_task(print, f"Backfilling {request.feature_view_id} from {request.start_date} to {request.end_date}")
    return {"status": "accepted", "message": "Backfill job submitted"}
