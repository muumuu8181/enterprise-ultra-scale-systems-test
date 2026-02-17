from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime, timezone
from src.models.pharmacy_models import Medication, Prescription, Dispensing, PrescriptionStatus
from src.schemas.pharmacy_schemas import MedicationCreate, PrescriptionCreate, DispensingCreate, InventoryUpdate

class PharmacyService:
    async def search_medications(self, db: AsyncSession, name: Optional[str] = None, drug_class: Optional[str] = None) -> List[Medication]:
        query = select(Medication)
        if name:
            query = query.where(Medication.name.ilike(f"%{name}%"))
        if drug_class:
            query = query.where(Medication.drug_class.ilike(f"%{drug_class}%"))
        result = await db.execute(query)
        return result.scalars().all()

    async def check_interactions(self, db: AsyncSession, medication_id: str) -> List[str]:
        # Mock implementation
        return ["Potential interaction with alcohol", "Take with food"]

    async def create_prescription(self, db: AsyncSession, prescription_in: PrescriptionCreate) -> Prescription:
        prescription = Prescription(**prescription_in.model_dump(exclude_unset=True))
        prescription.status = PrescriptionStatus.received
        db.add(prescription)
        await db.commit()
        await db.refresh(prescription)
        return prescription

    async def get_queue(self, db: AsyncSession, status: Optional[PrescriptionStatus] = None) -> List[Prescription]:
        query = select(Prescription)
        if status:
            query = query.where(Prescription.status == status)
        result = await db.execute(query)
        return result.scalars().all()

    async def fill_prescription(self, db: AsyncSession, dispensing_in: DispensingCreate) -> Dispensing:
        # Check if prescription exists
        query = select(Prescription).where(Prescription.id == dispensing_in.prescription_id)
        result = await db.execute(query)
        prescription = result.scalar_one_or_none()
        if not prescription:
            raise ValueError("Prescription not found")

        if prescription.status == PrescriptionStatus.cancelled:
            raise ValueError("Prescription is cancelled")

        # Refill logic
        if prescription.status in [PrescriptionStatus.filled, PrescriptionStatus.picked_up]:
            if prescription.refills_used >= prescription.refills_allowed:
                raise ValueError("No refills remaining")
            prescription.refills_used += 1

        # Check stock
        med_query = select(Medication).where(Medication.id == prescription.medication_id)
        med_result = await db.execute(med_query)
        medication = med_result.scalar_one_or_none()
        if not medication:
             raise ValueError("Medication not found")

        if medication.stock_quantity < dispensing_in.quantity:
            raise ValueError("Insufficient stock")

        # Create dispensing
        dispensing = Dispensing(**dispensing_in.model_dump(exclude_unset=True))
        db.add(dispensing)

        # Update stock
        medication.stock_quantity -= dispensing_in.quantity

        # Update prescription status
        prescription.status = PrescriptionStatus.filled

        await db.commit()
        await db.refresh(dispensing)
        return dispensing

    async def verify_dispensing(self, db: AsyncSession, dispensing_id: str) -> Dispensing:
        query = select(Dispensing).where(Dispensing.id == dispensing_id)
        result = await db.execute(query)
        dispensing = result.scalar_one_or_none()
        if not dispensing:
            raise ValueError("Dispensing not found")

        # Mark as counseled/verified
        dispensing.patient_counseled = True

        await db.commit()
        await db.refresh(dispensing)
        return dispensing

    async def check_low_stock(self, db: AsyncSession) -> List[Medication]:
        query = select(Medication).where(Medication.stock_quantity <= Medication.reorder_level)
        result = await db.execute(query)
        return result.scalars().all()

    async def reorder_inventory(self, db: AsyncSession, inventory_update: InventoryUpdate) -> Medication:
        query = select(Medication).where(Medication.id == inventory_update.medication_id)
        result = await db.execute(query)
        medication = result.scalar_one_or_none()
        if not medication:
            raise ValueError("Medication not found")

        medication.stock_quantity += inventory_update.quantity_change
        await db.commit()
        await db.refresh(medication)
        return medication

    async def get_analytics(self, db: AsyncSession, period: str) -> dict:
        # Mock analytics
        stmt = select(func.count(Dispensing.id), func.sum(Dispensing.copay_amount))
        result = await db.execute(stmt)
        count, revenue = result.one()

        return {
            "period": period,
            "total_dispensed": count or 0,
            "total_revenue": revenue or 0.0,
            "top_medications": ["Med A", "Med B"] # Mock
        }

pharmacy_service = PharmacyService()
