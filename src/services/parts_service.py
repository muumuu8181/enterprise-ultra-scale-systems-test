from src.db.session import AsyncSessionLocal
from src.models.work_order import WorkOrder, SparePart
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any

class OrderRecommendation(BaseModel):
    part_number: str
    recommended_qty: int
    reason: str

async def check_parts_availability(work_order_id: int) -> Dict[str, Any]:
    """
    Checks if parts required for a work order are available in stock.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
        work_order = result.scalar_one_or_none()

        if not work_order:
            return {"status": "error", "message": "Work order not found"}

        parts_needed = work_order.parts_needed or {}
        availability = {}
        missing_parts = []

        # In a real implementation, we would query SparePart table and check stock_qty
        # For now, we return a mock response

        return {
            "work_order_id": work_order_id,
            "status": "checked",
            "parts_availability": availability,
            "missing_parts": missing_parts
        }

async def optimize_spare_inventory(forecast_horizon: int) -> List[OrderRecommendation]:
    """
    Analyzes inventory and usage trends to recommend spare parts orders.
    """
    # Mock implementation
    # In reality, this would query historical usage, lead times, etc.

    recommendations = [
        OrderRecommendation(
            part_number="SP-001",
            recommended_qty=10,
            reason=f"Forecast demand increase over next {forecast_horizon} days"
        ),
        OrderRecommendation(
            part_number="SP-005",
            recommended_qty=2,
            reason="Safety stock below threshold"
        )
    ]
    return recommendations
