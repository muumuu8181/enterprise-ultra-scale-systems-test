from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.db.session import get_db
from src.models.mes_models import WorkOrder, ProductionLine, QualityCheck, WorkOrderStatus, ProductionLineStatus, QualityCheckResult
from src.services.oee_service import OEEService

router = APIRouter(prefix="/production", tags=["Production"])

# --- Schemas ---
class WorkOrderCreate(BaseModel):
    product_id: str
    quantity: int
    scheduled_start: datetime

class WorkOrderResponse(BaseModel):
    id: int
    product_id: str
    quantity: int
    scheduled_start: datetime
    actual_start: Optional[datetime] = None
    status: str
    defect_count: int

    model_config = ConfigDict(from_attributes=True)

class WorkOrderProgress(BaseModel):
    id: int
    status: str
    completion_percentage: float
    defect_rate: float

class StatusUpdate(BaseModel):
    status: str

class QualityCheckCreate(BaseModel):
    work_order_id: int
    checkpoint_name: str
    result: str
    measured_value: float
    spec_min: float
    spec_max: float

class QualityCheckResponse(BaseModel):
    id: int
    work_order_id: int
    checkpoint_name: str
    result: str
    measured_value: float
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OEEData(BaseModel):
    availability: float
    performance: float
    quality: float
    oee: float

# --- Dependencies ---
async def get_oee_service(db: AsyncSession = Depends(get_db)) -> OEEService:
    return OEEService(db)

# --- Endpoints ---

@router.post("/work-orders", response_model=WorkOrderResponse)
async def create_work_order(
    wo: WorkOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    new_wo = WorkOrder(
        product_id=wo.product_id,
        quantity=wo.quantity,
        scheduled_start=wo.scheduled_start,
        status=WorkOrderStatus.PLANNED.value
    )
    db.add(new_wo)
    await db.commit()
    await db.refresh(new_wo)
    return new_wo

@router.get("/work-orders/{id}/progress", response_model=WorkOrderProgress)
async def get_work_order_progress(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    wo = await db.get(WorkOrder, id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")

    # Calculate progress mock logic
    completion = 0.0
    if wo.status == WorkOrderStatus.COMPLETED.value:
        completion = 100.0
    elif wo.status == WorkOrderStatus.RUNNING.value:
        completion = 50.0 # Mock value

    defect_rate = 0.0
    if wo.quantity > 0:
        defect_rate = (wo.defect_count / wo.quantity) * 100

    return WorkOrderProgress(
        id=wo.id,
        status=wo.status,
        completion_percentage=completion,
        defect_rate=defect_rate
    )

@router.put("/work-orders/{id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    id: int,
    status_update: StatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    wo = await db.get(WorkOrder, id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")

    wo.status = status_update.status
    if status_update.status == WorkOrderStatus.RUNNING.value and not wo.actual_start:
        wo.actual_start = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(wo)
    return wo

@router.get("/production-lines/{id}/oee", response_model=OEEData)
async def get_production_line_oee(
    id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: OEEService = Depends(get_oee_service)
):
    if not date_from:
        date_from = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    if not date_to:
        date_to = datetime.now(timezone.utc)

    return await service.calculate_oee(id, (date_from, date_to))

@router.post("/quality-checks", response_model=QualityCheckResponse)
async def create_quality_check(
    qc: QualityCheckCreate,
    db: AsyncSession = Depends(get_db)
):
    wo = await db.get(WorkOrder, qc.work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")

    new_qc = QualityCheck(
        work_order_id=qc.work_order_id,
        checkpoint_name=qc.checkpoint_name,
        result=qc.result,
        measured_value=qc.measured_value,
        spec_min=qc.spec_min,
        spec_max=qc.spec_max
    )
    db.add(new_qc)

    if qc.result == QualityCheckResult.FAIL.value:
        wo.defect_count += 1

    await db.commit()
    await db.refresh(new_qc)
    return new_qc

@router.get("/quality-checks/defect-report")
async def get_defect_report(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(QualityCheck).where(
        and_(
            QualityCheck.checked_at >= date_from,
            QualityCheck.checked_at <= date_to,
            QualityCheck.result == QualityCheckResult.FAIL.value
        )
    )
    result = await db.execute(stmt)
    defects = result.scalars().all()

    return {
        "period": {"from": date_from, "to": date_to},
        "total_defects": len(defects),
        "details": [
            {
                "id": d.id,
                "work_order_id": d.work_order_id,
                "checkpoint": d.checkpoint_name,
                "measured": d.measured_value,
                "spec": f"{d.spec_min}-{d.spec_max}"
            } for d in defects
        ]
    }
