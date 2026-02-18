from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Dict
from src.services.grid_service import (
    detect_overload,
    calculate_optimal_dispatch,
    simulate_n_minus_1,
    Alert,
    DispatchPlan,
    StabilityReport
)

router = APIRouter(prefix="/grid", tags=["grid"])

@router.get("/real-time-state")
async def get_real_time_state():
    return {"status": "ok", "message": "Real-time state endpoint"}

@router.get("/nodes/{id}/metrics")
async def get_node_metrics(id: str = Path(..., title="The ID of the node")):
    alerts = await detect_overload(id)
    return {"node_id": id, "alerts": alerts}

@router.get("/congestion-map")
async def get_congestion_map():
    return {"message": "Congestion map endpoint"}

@router.post("/redispatch", response_model=DispatchPlan)
async def post_redispatch(demand: Dict[str, float] = Body(...)):
    return await calculate_optimal_dispatch(demand)

@router.post("/emergency-shutdown/{node_id}")
async def emergency_shutdown(node_id: str):
    return {"message": f"Emergency shutdown initiated for node {node_id}"}
