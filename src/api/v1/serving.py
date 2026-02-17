from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import time
import random
import json
from src.core.database import get_db
from src.models.serving_models import InferenceEndpoint, PredictionLog, ModelMonitorReport
from src.services import monitoring_service

router = APIRouter()

# --- Pydantic Schemas ---
class EndpointCreate(BaseModel):
    model_id: str
    endpoint_url: str
    auth_type: str = "api_key"

class EndpointResponse(BaseModel):
    id: int
    model_id: str
    endpoint_url: str
    auth_type: str

    class Config:
        from_attributes = True

class PredictionRequest(BaseModel):
    input_data: dict

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    latency_ms: float

class AlertRequest(BaseModel):
    endpoint_id: int
    metric: str
    threshold: float

class ABTestRequest(BaseModel):
    variant_b_url: str
    traffic_split: float

# --- Routes ---

@router.post("/endpoints/deploy", response_model=EndpointResponse)
async def deploy_endpoint(endpoint_in: EndpointCreate, db: AsyncSession = Depends(get_db)):
    """
    Deploys a new inference endpoint.
    Implements a mock blue-green deployment strategy.
    """
    # Logic to switch traffic or deploy container would go here.
    endpoint = InferenceEndpoint(
        model_id=endpoint_in.model_id,
        endpoint_url=endpoint_in.endpoint_url,
        auth_type=endpoint_in.auth_type,
        latency_p99_ms=0.0,
        throughput_rps=0.0,
        cost_per_1k=0.0
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return endpoint

@router.get("/endpoints/{id}/metrics")
async def get_endpoint_metrics(id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves metrics for a specific endpoint.
    """
    endpoint = await db.get(InferenceEndpoint, id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return {
        "latency_p99_ms": endpoint.latency_p99_ms,
        "throughput_rps": endpoint.throughput_rps,
        "cost_per_1k": endpoint.cost_per_1k
    }

@router.post("/endpoints/{id}/predict", response_model=PredictionResponse)
async def predict(id: int, request: PredictionRequest, db: AsyncSession = Depends(get_db)):
    """
    Proxies a prediction request to the underlying model and logs the result.
    """
    start_time = time.time()

    # Mock prediction call
    # In real world: response = requests.post(endpoint.url, json=request.input_data)
    prediction_result = "class_A"
    confidence = 0.95

    latency = (time.time() - start_time) * 1000

    # Log prediction
    log = PredictionLog(
        endpoint_id=id,
        request_id=f"req_{int(time.time())}",
        input_hash=str(hash(json.dumps(request.input_data))),
        prediction=prediction_result,
        confidence=confidence,
        latency_ms=latency
    )
    db.add(log)
    await db.commit()

    return PredictionResponse(
        prediction=prediction_result,
        confidence=confidence,
        latency_ms=latency
    )

@router.post("/endpoints/{id}/ab-test")
async def start_ab_test(id: int, ab_test: ABTestRequest):
    """
    Starts an A/B test for the endpoint.
    """
    return {"status": "started", "endpoint_id": id, "split": ab_test.traffic_split}

@router.get("/monitoring/{endpoint_id}/drift", response_model=monitoring_service.DriftReport)
async def get_drift_report(endpoint_id: int, window: str = "24h"):
    """
    Generates a data drift report.
    """
    report = await monitoring_service.detect_data_drift(endpoint_id, window)
    return report

@router.post("/monitoring/alerts")
async def configure_alert(alert: AlertRequest):
    """
    Configures an alert for model monitoring.
    """
    # Logic to save alert configuration
    # Also triggers auto-rollback check as a test
    rollback_status = await monitoring_service.auto_rollback(alert.endpoint_id, alert.metric, alert.threshold)
    return {"alert_configured": True, "rollback_check": rollback_status}
