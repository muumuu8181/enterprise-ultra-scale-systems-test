from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.quantum_service import quantum_service
from src.schemas.quantum_schemas import (
    QuantumCircuitCreate, QuantumCircuitResponse,
    SimulationJobCreate, SimulationJobResponse,
    QuantumAlgorithmCreate, QuantumAlgorithmResponse
)
from src.models.quantum_models import QuantumBackend, AlgorithmType
from typing import List, Dict, Any, Optional

router = APIRouter()

@router.post("/circuits/create", response_model=QuantumCircuitResponse)
async def create_circuit(
    circuit_in: QuantumCircuitCreate,
    db: AsyncSession = Depends(get_db)
):
    # Mock creator_id
    return await quantum_service.create_circuit(db, circuit_in, creator_id="user_1")

@router.get("/circuits/{circuit_id}/visualize")
async def visualize_circuit(
    circuit_id: int,
    db: AsyncSession = Depends(get_db)
):
    circuit = await quantum_service.get_circuit(db, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")

    # Mock visualization (ASCII art or similar)
    return {
        "circuit_id": circuit_id,
        "visualization": f"|0> -- H -- [ {circuit.name} ] -- M --"
    }

@router.post("/simulations/run", response_model=SimulationJobResponse)
async def run_simulation(
    job_in: SimulationJobCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await quantum_service.create_simulation_job(db, job_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/simulations/{job_id}/result", response_model=SimulationJobResponse)
async def get_simulation_result(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    job = await quantum_service.get_simulation_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/simulations/{job_id}/statevector")
async def get_simulation_statevector(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    job = await quantum_service.get_simulation_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Mock statevector
    return {"statevector": [0.707 + 0j, 0.707 + 0j, 0, 0]}

@router.get("/simulations/{job_id}/histogram")
async def get_simulation_histogram(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    job = await quantum_service.get_simulation_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Mock histogram
    return {"counts": {"00": 512, "11": 512}}

@router.get("/algorithms", response_model=List[QuantumAlgorithmResponse])
async def list_algorithms(
    type: Optional[str] = Query(None, description="Filter by algorithm type"),
    db: AsyncSession = Depends(get_db)
):
    return await quantum_service.list_algorithms(db, type)

@router.post("/algorithms/{algorithm_id}/instantiate", response_model=QuantumCircuitResponse)
async def instantiate_algorithm(
    algorithm_id: int,
    parameters: Dict[str, Any] = Body(default={}),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Mock creator_id
        return await quantum_service.instantiate_algorithm(db, algorithm_id, creator_id="user_1")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/backends/available")
async def list_backends():
    return {"backends": [b.value for b in QuantumBackend]}

@router.get("/analytics/job-queue-status")
async def job_queue_status():
    # Mock queue status
    return {"queued_jobs": 5, "running_jobs": 2, "avg_wait_time_ms": 1200}

@router.post("/algorithms", response_model=QuantumAlgorithmResponse)
async def create_algorithm(
    algo_in: QuantumAlgorithmCreate,
    db: AsyncSession = Depends(get_db)
):
    return await quantum_service.create_algorithm(db, algo_in)
