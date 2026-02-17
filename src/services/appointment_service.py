from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.campaign_models import AppointmentSlot
from datetime import datetime, timezone

class AppointmentBooking:
    def __init__(self, slot_id: int, patient_id: str, status: str):
        self.slot_id = slot_id
        self.patient_id = patient_id
        self.status = status

async def book_appointment(db: AsyncSession, patient_id: str, slot_id: int) -> AppointmentBooking:
    stmt = select(AppointmentSlot).where(AppointmentSlot.id == slot_id)
    result = await db.execute(stmt)
    slot = result.scalar_one_or_none()

    if not slot:
        return AppointmentBooking(slot_id, patient_id, "FAILED_NOT_FOUND")

    if not slot.available:
        return AppointmentBooking(slot_id, patient_id, "FAILED_ALREADY_BOOKED")

    slot.available = False
    slot.booked_patient_id = patient_id
    await db.commit()
    await db.refresh(slot)

    return AppointmentBooking(slot_id, patient_id, "CONFIRMED")

async def generate_reminder(appointment_id: int):
    print(f"Generating reminder for appointment {appointment_id}")
    return True

async def calculate_herd_immunity(region: str) -> float:
    # Mock implementation
    return 0.75
