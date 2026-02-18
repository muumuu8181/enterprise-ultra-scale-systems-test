from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from src.models.vaccine_models import VaccineBatch, DistributionCenter
from src.services import distribution_service
from src.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter()

class BatchReceiveRequest(BaseModel):
    vaccine_type: str
    manufacturer: str
    lot_number: str
    quantity: int
    expiry_date: datetime
    cold_chain_required: bool = True
    current_location_id: int

class TransferRequest(BaseModel):
    destination_location_id: int
    quantity: int

@router.post("/batches/receive")
async def receive_batch(request: BatchReceiveRequest, db: AsyncSession = Depends(get_db)):
    # Logic to create a new batch record
    new_batch = VaccineBatch(
        vaccine_type=request.vaccine_type,
        manufacturer=request.manufacturer,
        lot_number=request.lot_number,
        quantity=request.quantity,
        expiry_date=request.expiry_date,
        cold_chain_required=request.cold_chain_required,
        current_location_id=request.current_location_id
    )
    db.add(new_batch)
    await db.commit()
    await db.refresh(new_batch)
    return new_batch

@router.get("/batches/{id}/chain-of-custody")
async def get_chain_of_custody(id: int):
    # Mock response for chain of custody
    return {"batch_id": id, "history": ["Manufacturer", "Central Hub", "Regional Center"]}

@router.get("/batches/expiring-soon")
async def get_expiring_soon():
    # Logic to query batches expiring soon
    # Mock response
    return [{"batch_id": 1, "expiry_date": "2024-12-31T23:59:59Z"}]

@router.post("/batches/{id}/transfer")
async def transfer_batch(id: int, request: TransferRequest):
    # Logic to transfer batch
    return {"status": "transfer_initiated", "batch_id": id, "destination": request.destination_location_id}

@router.get("/batches/{id}/temperature-log")
async def get_temperature_log(id: int):
    return await distribution_service.track_cold_chain(id)

@router.get("/inventory/current")
async def get_current_inventory():
    # Logic to get inventory
    return {"total_doses": 5000, "by_type": {"Pfizer": 3000, "Moderna": 2000}}
