from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.warehouse_models import PickList as PickListModel, StorageLocation as StorageLocationModel, ReplenishmentOrder as ReplenishmentOrderModel, PickListStatus, TriggerType
from src.services.wms_service import WMSService, CycleCountResult
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional, Any

router = APIRouter()

# --- Schemas ---

class PickListBase(BaseModel):
    order_id: str
    items: Dict[str, int]
    assigned_robot_id: Optional[str] = None
    status: PickListStatus
    completion_pct: float

class PickListRead(PickListBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PickListRequest(BaseModel):
    order_id: str

class InventoryUpdateRequest(BaseModel):
    quantity_change: int

class ReplenishmentTriggerRequest(BaseModel):
    sku: str
    from_zone: str
    to_zone: str
    quantity: int
    triggered_by: TriggerType

class ReplenishmentRead(BaseModel):
    id: int
    sku: str
    from_zone: str
    to_zone: str
    quantity: int
    triggered_by: TriggerType
    model_config = ConfigDict(from_attributes=True)

class HeatmapItem(BaseModel):
    location_id: int
    zone_id: str
    quantity: int

# --- Endpoints ---

@router.post("/pick-lists/generate", response_model=PickListRead)
async def generate_pick_list(request: PickListRequest, db: AsyncSession = Depends(get_db)):
    service = WMSService(db)
    result = await service.generate_pick_list(request.order_id)
    return result

@router.get("/pick-lists/{id}/progress")
async def get_pick_list_progress(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(PickListModel, id)
    if not result:
        raise HTTPException(status_code=404, detail="Pick list not found")
    return {"id": result.id, "status": result.status, "completion_pct": result.completion_pct}

@router.post("/locations/{id}/inventory-update")
async def update_inventory(id: int, request: InventoryUpdateRequest, db: AsyncSession = Depends(get_db)):
    location = await db.get(StorageLocationModel, id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    location.quantity += request.quantity_change
    # Ensure quantity doesn't go below 0
    if location.quantity < 0:
        location.quantity = 0

    await db.commit()
    await db.refresh(location)
    return {"id": location.id, "new_quantity": location.quantity}

@router.get("/locations/heatmap", response_model=List[HeatmapItem])
async def get_heatmap(db: AsyncSession = Depends(get_db)):
    # Simple query for all locations with quantities
    result = await db.execute(select(StorageLocationModel))
    locations = result.scalars().all()
    return [
        HeatmapItem(location_id=loc.id, zone_id=loc.zone_id, quantity=loc.quantity)
        for loc in locations
    ]

@router.post("/replenishment/trigger", response_model=ReplenishmentRead)
async def trigger_replenishment(request: ReplenishmentTriggerRequest, db: AsyncSession = Depends(get_db)):
    new_order = ReplenishmentOrderModel(
        sku=request.sku,
        from_zone=request.from_zone,
        to_zone=request.to_zone,
        quantity=request.quantity,
        triggered_by=request.triggered_by
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order

@router.get("/replenishment/pending", response_model=List[ReplenishmentRead])
async def get_pending_replenishments(db: AsyncSession = Depends(get_db)):
    # Assuming all present are pending as there is no status field in the prompt's ReplenishmentOrder model
    result = await db.execute(select(ReplenishmentOrderModel))
    orders = result.scalars().all()
    return orders
