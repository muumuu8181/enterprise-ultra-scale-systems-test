from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.services.parts_service import check_parts_availability, optimize_spare_inventory, OrderRecommendation
from typing import List, Dict, Any

router = APIRouter()

@router.post("/work-orders/auto-generate")
async def auto_generate_work_orders(db: AsyncSession = Depends(get_db)):
    """
    Triggers automatic generation of work orders based on equipment sensor data.
    """
    return {"message": "Auto-generation triggered", "generated_count": 0}

@router.get("/work-orders/schedule")
async def get_work_order_schedule(db: AsyncSession = Depends(get_db)):
    """
    Retrieves the current maintenance schedule.
    """
    return {"schedule": []}

@router.get("/work-orders/{id}/parts-availability")
async def get_parts_availability(id: int):
    """
    Checks availability of parts for a specific work order.
    """
    result = await check_parts_availability(id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Work order not found"))
    return result

@router.post("/work-orders/{id}/complete")
async def complete_work_order(id: int, db: AsyncSession = Depends(get_db)):
    """
    Marks a work order as complete.
    """
    return {"id": id, "status": "completed"}

@router.post("/spare-parts/order")
async def order_spare_parts(order_details: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Places an order for spare parts.
    """
    return {"order_id": "ORD-123", "status": "placed", "details": order_details}

@router.get("/spare-parts/inventory-optimization", response_model=List[OrderRecommendation])
async def get_inventory_optimization(forecast_horizon: int = 30):
    """
    Returns inventory optimization recommendations based on forecast horizon.
    """
    recommendations = await optimize_spare_inventory(forecast_horizon)
    return recommendations
