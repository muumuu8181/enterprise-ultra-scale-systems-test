from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database import get_db
from src.models.campaign_models import VaccinationCampaign, AppointmentSlot
from src.services.appointment_service import book_appointment, calculate_herd_immunity

router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    target_population: int
    vaccine_type: str
    start_date: datetime
    end_date: datetime

class AppointmentBookRequest(BaseModel):
    patient_id: str
    slot_id: int

@router.post("/campaigns/create")
async def create_campaign(campaign: CampaignCreate, db: AsyncSession = Depends(get_db)):
    new_campaign = VaccinationCampaign(**campaign.dict())
    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign)
    return new_campaign

@router.get("/campaigns/{id}/progress")
async def get_campaign_progress(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(VaccinationCampaign).where(VaccinationCampaign.id == id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {
        "doses_administered": campaign.doses_administered,
        "coverage_pct": campaign.coverage_pct,
        "herd_immunity_estimate": await calculate_herd_immunity("global")
    }

@router.get("/appointments/available")
async def get_available_appointments(
    vaccine: Optional[str] = None,
    date: Optional[datetime] = None,
    zip_code: Optional[str] = Query(None, alias="zip"),
    db: AsyncSession = Depends(get_db)
):
    # Note: zip_code filtering is requested but AppointmentSlot model does not have location data.
    # In a real implementation, we would join with a Site model or filter by site_id.
    stmt = select(AppointmentSlot).where(AppointmentSlot.available == True)
    if vaccine:
        stmt = stmt.where(AppointmentSlot.vaccine_type == vaccine)
    if date:
        stmt = stmt.where(AppointmentSlot.date >= date)

    result = await db.execute(stmt)
    slots = result.scalars().all()
    return slots

@router.post("/appointments/book")
async def book_appointment_endpoint(request: AppointmentBookRequest, db: AsyncSession = Depends(get_db)):
    booking = await book_appointment(db, request.patient_id, request.slot_id)
    if booking.status != "CONFIRMED":
        raise HTTPException(status_code=400, detail=booking.status)
    return {"slot_id": booking.slot_id, "status": booking.status}

@router.post("/appointments/{id}/checkin")
async def checkin_appointment(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(AppointmentSlot).where(AppointmentSlot.id == id)
    result = await db.execute(stmt)
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    # Update campaign stats
    # Find active campaign for this vaccine type
    campaign_stmt = select(VaccinationCampaign).where(
        VaccinationCampaign.vaccine_type == slot.vaccine_type
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if campaign:
        campaign.doses_administered += 1
        if campaign.target_population > 0:
            campaign.coverage_pct = (campaign.doses_administered / campaign.target_population) * 100
        await db.commit()
        await db.refresh(campaign)

    return {"status": "checked_in", "vaccine_type": slot.vaccine_type}

@router.get("/patients/{id}/vaccination-record")
async def get_patient_record(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AppointmentSlot).where(AppointmentSlot.booked_patient_id == id)
    result = await db.execute(stmt)
    slots = result.scalars().all()
    return {"patient_id": id, "appointments": slots}
