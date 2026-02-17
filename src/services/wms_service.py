from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.warehouse_models import PickList, StorageLocation, ReplenishmentOrder, PickListStatus, TriggerType
from pydantic import BaseModel
from typing import List, Optional, Dict

class CycleCountResult(BaseModel):
    zone_id: str
    total_items_counted: int
    discrepancies_found: int
    accuracy_rate: float

class WMSService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_pick_list(self, order_id: str) -> PickList:
        # Mock items since we don't have an Order model
        mock_items = {"SKU001": 2, "SKU002": 1}

        new_pick_list = PickList(
            order_id=order_id,
            items=mock_items,
            status=PickListStatus.PENDING,
            completion_pct=0.0
        )
        self.db.add(new_pick_list)
        await self.db.commit()
        await self.db.refresh(new_pick_list)
        return new_pick_list

    async def optimize_storage_placement(self, sku: str, quantity: int) -> StorageLocation:
        # Simple logic: find a location with same SKU or empty bin
        stmt = select(StorageLocation).where(StorageLocation.sku == sku)
        result = await self.db.execute(stmt)
        location = result.scalars().first()

        if not location:
            # Create a new location in a default spot if none exists
            location = StorageLocation(
                zone_id="Z1",
                aisle="A1",
                rack="R1",
                level="L1",
                bin="B1",
                sku=sku,
                quantity=quantity,
                reserved_qty=0
            )
            self.db.add(location)
        else:
            location.quantity += quantity

        await self.db.commit()
        await self.db.refresh(location)
        return location

    async def run_cycle_count(self, zone_id: str) -> CycleCountResult:
        stmt = select(func.count(StorageLocation.id)).where(StorageLocation.zone_id == zone_id)
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        # Mock discrepancy calculation
        discrepancies = 0
        accuracy = 100.0

        return CycleCountResult(
            zone_id=zone_id,
            total_items_counted=count,
            discrepancies_found=discrepancies,
            accuracy_rate=accuracy
        )
