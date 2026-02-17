from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone

from src.database import get_db
from src.models.pharmacy_models import Medication, Dispensing
from src.services.drug_interaction_checker import check_interactions

router = APIRouter()

# Pydantic Schemas
class MedicationRead(BaseModel):
    id: int
    name: str
    generic_name: str
    category: str
    dosage_form: str
    stock_quantity: int
    reorder_threshold: int

    model_config = ConfigDict(from_attributes=True)

class DispenseRequest(BaseModel):
    medication_id: int
    pharmacist_id: int
    quantity: int = Field(..., gt=0)
    batch_number: str

class DispensingRead(BaseModel):
    id: int
    prescription_id: int
    pharmacist_id: int
    dispensed_at: datetime
    quantity: int
    batch_number: str

    model_config = ConfigDict(from_attributes=True)

class ReorderRequest(BaseModel):
    medication_id: int
    quantity: int = Field(..., gt=0)

class PrescriptionPending(BaseModel):
    id: int
    patient_name: str
    medication_name: str
    status: str
    created_at: datetime


# Endpoints

@router.get("/pharmacy/medications", response_model=List[MedicationRead])
async def search_medications(
    search: Optional[str] = Query(None, description="Search by name or generic name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Medication)
    if search:
        query = query.where(
            (Medication.name.ilike(f"%{search}%")) |
            (Medication.generic_name.ilike(f"%{search}%"))
        )
    if category:
        query = query.where(Medication.category == category)

    result = await db.execute(query)
    medications = result.scalars().all()
    return medications

@router.post("/pharmacy/prescriptions/{prescription_id}/dispense", response_model=DispensingRead)
async def dispense_medication(
    prescription_id: int,
    request: DispenseRequest,
    db: AsyncSession = Depends(get_db)
):
    # Check interaction (example usage)
    # interactions = await check_interactions([request.medication_id])
    # if interactions:
    #     pass # Handle logic if needed, currently just logging or ignoring based on requirements

    # Fetch medication with lock to update stock
    result = await db.execute(
        select(Medication).where(Medication.id == request.medication_id).with_for_update()
    )
    medication = result.scalar_one_or_none()

    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    if medication.stock_quantity < request.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Current: {medication.stock_quantity}")

    # Update stock
    medication.stock_quantity -= request.quantity

    # Record dispensing
    dispensing = Dispensing(
        prescription_id=prescription_id,
        pharmacist_id=request.pharmacist_id,
        quantity=request.quantity,
        batch_number=request.batch_number,
        dispensed_at=datetime.now(timezone.utc)
    )
    db.add(dispensing)

    await db.commit()
    await db.refresh(dispensing)

    return dispensing

@router.get("/pharmacy/prescriptions/pending", response_model=List[PrescriptionPending])
async def get_pending_prescriptions():
    # Mock implementation as Prescription model is not defined
    return [
        PrescriptionPending(
            id=101,
            patient_name="John Doe",
            medication_name="Amoxicillin",
            status="pending",
            created_at=datetime.now(timezone.utc)
        ),
        PrescriptionPending(
            id=102,
            patient_name="Jane Smith",
            medication_name="Ibuprofen",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
    ]

@router.post("/pharmacy/inventory/reorder")
async def reorder_inventory(
    request: ReorderRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Medication).where(Medication.id == request.medication_id).with_for_update()
    )
    medication = result.scalar_one_or_none()

    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")

    medication.stock_quantity += request.quantity
    await db.commit()

    return {"message": "Reorder successful", "new_stock_quantity": medication.stock_quantity}
