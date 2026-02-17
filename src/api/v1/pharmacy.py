from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.services.pharmacy_service import pharmacy_service
from src.schemas.pharmacy_schemas import (
    MedicationResponse, PrescriptionResponse, PrescriptionCreate,
    DispensingResponse, DispensingCreate, InventoryUpdate, AnalyticsResponse
)
from src.models.pharmacy_models import PrescriptionStatus

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])

@router.get("/medications/search", response_model=List[MedicationResponse])
async def search_medications(
    name: Optional[str] = None,
    drug_class: Optional[str] = Query(None, alias="class"),
    db: AsyncSession = Depends(get_db)
):
    return await pharmacy_service.search_medications(db, name, drug_class)

@router.get("/medications/{id}/interactions", response_model=List[str])
async def check_interactions(id: str, db: AsyncSession = Depends(get_db)):
    return await pharmacy_service.check_interactions(db, id)

@router.post("/prescriptions/receive", response_model=PrescriptionResponse)
async def receive_prescription(prescription: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
    return await pharmacy_service.create_prescription(db, prescription)

@router.get("/prescriptions/queue", response_model=List[PrescriptionResponse])
async def get_queue(status: Optional[PrescriptionStatus] = None, db: AsyncSession = Depends(get_db)):
    return await pharmacy_service.get_queue(db, status)

@router.post("/dispensing/fill", response_model=DispensingResponse)
async def fill_prescription(dispensing: DispensingCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await pharmacy_service.fill_prescription(db, dispensing)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dispensing/{id}/verify", response_model=DispensingResponse)
async def verify_dispensing(id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await pharmacy_service.verify_dispensing(db, id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/inventory/low-stock", response_model=List[MedicationResponse])
async def check_low_stock(db: AsyncSession = Depends(get_db)):
    return await pharmacy_service.check_low_stock(db)

@router.post("/inventory/reorder", response_model=MedicationResponse)
async def reorder_inventory(update: InventoryUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await pharmacy_service.reorder_inventory(db, update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/analytics/dispensing-volume", response_model=AnalyticsResponse)
async def get_analytics(period: str, db: AsyncSession = Depends(get_db)):
    data = await pharmacy_service.get_analytics(db, period)
    return AnalyticsResponse(**data)
