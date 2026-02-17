from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from src.models.semiconductor_models import WaferSize, LotStatus, EquipmentType, EquipmentStatus

router = APIRouter(prefix="/semiconductor", tags=["Semiconductor"])

# Schemas
class WaferLotBase(BaseModel):
    lot_number: str
    wafer_size_mm: int
    process_node_nm: int
    product: str
    quantity: int
    current_step: str
    priority: int = 1
    status: str
    model_config = ConfigDict(from_attributes=True)

class WaferLotCreate(WaferLotBase):
    pass

class WaferLotResponse(WaferLotBase):
    id: int
    yield_pct: Optional[float] = None

class EquipmentBase(BaseModel):
    name: str
    equipment_type: str
    chamber_count: int
    status: str
    utilization_pct: float = 0.0
    model_config = ConfigDict(from_attributes=True)

class EquipmentResponse(EquipmentBase):
    id: int
    pm_due_date: Optional[datetime] = None

class ProcessStepBase(BaseModel):
    step_name: str
    recipe: str
    measurements: Dict[str, Any]
    pass_fail: bool
    operator_id: str
    model_config = ConfigDict(from_attributes=True)

class ProcessStepCreate(ProcessStepBase):
    lot_id: int
    equipment_id: int

class ProcessStepResponse(ProcessStepBase):
    id: int
    lot_id: int
    equipment_id: int
    start_time: datetime
    end_time: Optional[datetime] = None

class YieldTrend(BaseModel):
    period: str
    average_yield: float

class WaferMap(BaseModel):
    lot_id: int
    map_data: Dict[str, Any]

class CapacityForecast(BaseModel):
    week: str
    available_capacity: float

# Endpoints

@router.get("/lots", response_model=List[WaferLotResponse])
async def get_lots(
    status: Optional[str] = None,
    product: Optional[str] = None
):
    return []

@router.get("/lots/{id}/traveler", response_model=WaferLotResponse)
async def get_lot_traveler(id: int = Path(...)):
    return WaferLotResponse(
        id=id,
        lot_number="LOT-001",
        wafer_size_mm=300,
        process_node_nm=5,
        product="CPU-X",
        quantity=25,
        current_step="Etch",
        priority=1,
        status="in_process"
    )

@router.get("/equipment", response_model=List[EquipmentResponse])
async def get_equipment(
    type: Optional[str] = None,
    status: Optional[str] = None
):
    return []

@router.post("/equipment/{id}/start-pm")
async def start_pm(id: int):
    return {"message": f"PM started for equipment {id}"}

@router.get("/steps/{lot_id}/history", response_model=List[ProcessStepResponse])
async def get_lot_history(lot_id: int):
    return []

@router.post("/steps/log-measurement", response_model=ProcessStepResponse)
async def log_measurement(step: ProcessStepCreate):
    return ProcessStepResponse(
        id=1,
        lot_id=step.lot_id,
        equipment_id=step.equipment_id,
        step_name=step.step_name,
        recipe=step.recipe,
        measurements=step.measurements,
        pass_fail=step.pass_fail,
        operator_id=step.operator_id,
        start_time=datetime.now(timezone.utc)
    )

@router.get("/yield/trend", response_model=List[YieldTrend])
async def get_yield_trend(
    product: Optional[str] = None,
    period: Optional[str] = "weekly"
):
    return [YieldTrend(period="2023-W40", average_yield=98.5)]

@router.get("/yield/wafer-map/{lot_id}", response_model=WaferMap)
async def get_wafer_map(lot_id: int):
    return WaferMap(lot_id=lot_id, map_data={"x": [], "y": [], "value": []})

@router.get("/capacity/forecast", response_model=List[CapacityForecast])
async def get_capacity_forecast(weeks: int = 4):
    return [CapacityForecast(week=f"Week {i}", available_capacity=100.0) for i in range(1, weeks + 1)]
