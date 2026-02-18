from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.twin_service import TwinService
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

router = APIRouter(prefix="/twins", tags=["Digital Twins"])

# Pydantic Schemas
class TwinCreate(BaseModel):
    physical_asset_id: str
    asset_type: str
    model_uri: str
    sync_interval_sec: int = 60

class TwinResponse(BaseModel):
    id: int
    physical_asset_id: str
    asset_type: str
    model_uri: str
    last_sync: Optional[datetime]
    sync_interval_sec: int

    model_config = ConfigDict(from_attributes=True)

class StateCreate(BaseModel):
    state_data: Dict[str, Any]

class StateResponse(BaseModel):
    id: int
    twin_id: int
    timestamp: datetime
    state_data: Dict[str, Any]
    simulation_mode: str

    model_config = ConfigDict(from_attributes=True)

class PredictionResponse(BaseModel):
    twin_id: int
    timestamp: datetime
    state_data: Dict[str, Any]
    simulation_mode: str

    model_config = ConfigDict(from_attributes=True)

class SimulationCreate(BaseModel):
    scenario_name: str
    parameters: Dict[str, Any]

class SimulationResponse(BaseModel):
    id: int
    twin_id: int
    scenario_name: str
    parameters: Dict[str, Any]
    status: str
    result_uri: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

async def run_simulation_background(simulation_id: int):
    # Create a fresh session for the background task
    from src.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        service = TwinService(session)
        # Fetch the simulation object
        sim = await service.get_simulation(simulation_id)
        if sim:
             await service.run_simulation(sim)

# API Endpoints
@router.post("/register", response_model=TwinResponse)
async def register_twin(twin_in: TwinCreate, db: AsyncSession = Depends(get_db)):
    service = TwinService(db)
    return await service.register_twin(
        physical_asset_id=twin_in.physical_asset_id,
        asset_type=twin_in.asset_type,
        model_uri=twin_in.model_uri,
        sync_interval_sec=twin_in.sync_interval_sec
    )

@router.get("/{id}/current-state", response_model=Optional[StateResponse])
async def get_current_state(id: int, db: AsyncSession = Depends(get_db)):
    service = TwinService(db)
    state = await service.get_current_state(id)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state

@router.post("/{id}/sync", response_model=StateResponse)
async def sync_twin(id: int, state_in: StateCreate, db: AsyncSession = Depends(get_db)):
    service = TwinService(db)
    try:
        return await service.sync_physical_to_digital(id, state_in.state_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{id}/history", response_model=List[StateResponse])
async def get_twin_history(
    id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    service = TwinService(db)
    return await service.get_history(id, from_date, to_date)

@router.post("/{id}/simulate", response_model=SimulationResponse)
async def run_simulation(
    id: int,
    sim_in: SimulationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    service = TwinService(db)
    # Check if twin exists
    twin = await service.get_twin(id)
    if not twin:
        raise HTTPException(status_code=404, detail="Twin not found")

    sim = await service.create_simulation(id, sim_in.scenario_name, sim_in.parameters)

    # Run in background using the standalone function
    background_tasks.add_task(run_simulation_background, sim.id)

    return sim

@router.get("/simulations/{id}/results", response_model=SimulationResponse)
async def get_simulation_results(id: int, db: AsyncSession = Depends(get_db)):
    service = TwinService(db)
    sim = await service.get_simulation(id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim

@router.get("/{id}/anomalies")
async def get_anomalies(id: int, db: AsyncSession = Depends(get_db)):
    service = TwinService(db)
    return await service.detect_anomaly(id)

@router.get("/{id}/prediction", response_model=PredictionResponse)
async def get_prediction(id: int, horizon_min: int = 60, db: AsyncSession = Depends(get_db)):
    service = TwinService(db)
    try:
        return await service.predict_future_state(id, horizon_min)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
