from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models.mes_models import WorkOrder, ProductionLine, WorkOrderStatus

class OEEService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_oee(self, line_id: int, date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        """
        Calculate OEE (Availability, Performance, Quality) for a production line.
        """
        start_date, end_date = date_range

        # Ensure dates are timezone-aware if not already
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        # 1. Get Production Line info
        line = await self.db.get(ProductionLine, line_id)
        if not line:
            return {"availability": 0.0, "performance": 0.0, "quality": 0.0, "oee": 0.0}

        # 2. Get Work Orders in range (completed or running)
        stmt = select(WorkOrder).where(
            and_(
                WorkOrder.actual_start >= start_date,
                WorkOrder.actual_start <= end_date,
                WorkOrder.status.in_([WorkOrderStatus.COMPLETED.value, WorkOrderStatus.RUNNING.value])
            )
        )
        result = await self.db.execute(stmt)
        work_orders = result.scalars().all()

        if not work_orders:
             return {"availability": 0.0, "performance": 0.0, "quality": 0.0, "oee": 0.0}

        # Calculations (Simplified Logic)

        total_quantity_produced = sum(wo.quantity for wo in work_orders)
        total_defects = sum(wo.defect_count for wo in work_orders)
        good_count = total_quantity_produced - total_defects

        # Quality = (Total - Defects) / Total
        quality = (good_count / total_quantity_produced) if total_quantity_produced > 0 else 0.0

        # Performance approximation
        total_time_seconds = (end_date - start_date).total_seconds()
        theoretical_max_production = (total_time_seconds / 3600) * line.capacity_per_hour
        performance = (total_quantity_produced / theoretical_max_production) if theoretical_max_production > 0 else 0.0
        performance = min(performance, 1.0)

        # Availability approximation (mock constant for demo unless we have downtime logs)
        availability = 0.95

        oee = availability * performance * quality

        return {
            "availability": round(availability, 4),
            "performance": round(performance, 4),
            "quality": round(quality, 4),
            "oee": round(oee, 4)
        }

    async def predict_maintenance(self, line_id: int) -> Dict[str, Any]:
        """
        Predict maintenance needs for a production line.
        """
        line = await self.db.get(ProductionLine, line_id)
        if not line:
            return {"error": "Line not found"}

        # Mock prediction logic
        if line.oee_score < 0.5:
             status = "Critical"
             days_to_maintenance = 0
             confidence = 0.95
        elif line.oee_score < 0.75:
             status = "Warning"
             days_to_maintenance = 3
             confidence = 0.80
        else:
             status = "Healthy"
             days_to_maintenance = 30
             confidence = 0.90

        return {
            "line_id": line_id,
            "predicted_status": status,
            "recommended_maintenance_date": (datetime.now(timezone.utc) + timedelta(days=days_to_maintenance)).isoformat(),
            "confidence_score": confidence
        }
