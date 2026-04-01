from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime, time

from src.database import get_db
from src.models.broadcast_models import (
    Channel, Program, AdSlot,
    ChannelType, ChannelStatus, ProgramStatus, AdSlotStatus
)
from src.schemas.broadcast_schemas import (
    ChannelCreate, ChannelResponse,
    ProgramCreate, ProgramResponse,
    AdSlotCreate, AdSlotResponse, AdSlotBookRequest,
    AnalyticsViewership, AnalyticsAdPerformance
)
from sqlalchemy import select, and_

router = APIRouter(prefix="/broadcast", tags=["broadcast"])

@router.get("/channels", response_model=List[ChannelResponse])
async def get_channels(
    type: Optional[ChannelType] = None,
    region: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Channel)
    if type:
        query = query.filter(Channel.channel_type == type)
    if region:
        query = query.filter(Channel.region == region)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/channels/create", response_model=ChannelResponse)
async def create_channel(channel: ChannelCreate, db: AsyncSession = Depends(get_db)):
    new_channel = Channel(**channel.model_dump())
    db.add(new_channel)
    await db.commit()
    await db.refresh(new_channel)
    return new_channel

@router.get("/schedule/{channel_id}", response_model=List[ProgramResponse])
async def get_schedule(
    channel_id: int,
    target_date: Optional[date] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Program).filter(Program.channel_id == channel_id)
    if target_date:
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)
        query = query.filter(and_(Program.scheduled_at >= start_of_day, Program.scheduled_at <= end_of_day))

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/programs/schedule", response_model=ProgramResponse)
async def schedule_program(program: ProgramCreate, db: AsyncSession = Depends(get_db)):
    # Check if channel exists
    channel = await db.execute(select(Channel).filter(Channel.id == program.channel_id))
    if not channel.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Channel not found")

    new_program = Program(**program.model_dump())
    db.add(new_program)
    await db.commit()
    await db.refresh(new_program)
    return new_program

@router.get("/adslots/available", response_model=List[AdSlotResponse])
async def get_available_adslots(
    program_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(AdSlot).filter(AdSlot.status == AdSlotStatus.AVAILABLE)
    if program_id:
        query = query.filter(AdSlot.program_id == program_id)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/adslots/book", response_model=AdSlotResponse)
async def book_adslot(
    booking: AdSlotBookRequest,
    db: AsyncSession = Depends(get_db)
):
    query = select(AdSlot).filter(AdSlot.id == booking.adslot_id)
    result = await db.execute(query)
    adslot = result.scalar_one_or_none()

    if not adslot:
        raise HTTPException(status_code=404, detail="AdSlot not found")

    if adslot.status != AdSlotStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="AdSlot not available")

    adslot.advertiser_id = booking.advertiser_id
    adslot.creative_url = booking.creative_url
    adslot.status = AdSlotStatus.BOOKED

    await db.commit()
    await db.refresh(adslot)
    return adslot

@router.post("/programs/{id}/go-live", response_model=ProgramResponse)
async def go_live(id: int, db: AsyncSession = Depends(get_db)):
    query = select(Program).filter(Program.id == id)
    result = await db.execute(query)
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    program.status = ProgramStatus.LIVE
    await db.commit()
    await db.refresh(program)
    return program

@router.get("/analytics/viewership/{program_id}", response_model=AnalyticsViewership)
async def get_viewership_analytics(program_id: int, db: AsyncSession = Depends(get_db)):
    # Mock data
    return AnalyticsViewership(
        program_id=program_id,
        viewers=15000,
        peak_viewers=20000,
        avg_watch_time_min=25.5
    )

@router.get("/analytics/ad-performance", response_model=List[AnalyticsAdPerformance])
async def get_ad_performance(db: AsyncSession = Depends(get_db)):
    # Mock data
    return [
        AnalyticsAdPerformance(
            ad_slot_id=1,
            impressions=5000,
            clicks=150,
            ctr=3.0
        ),
        AnalyticsAdPerformance(
            ad_slot_id=2,
            impressions=4500,
            clicks=200,
            ctr=4.4
        )
    ]

@router.post("/adslots/create", response_model=AdSlotResponse)
async def create_adslot(adslot: AdSlotCreate, db: AsyncSession = Depends(get_db)):
    # Check if program exists
    program = await db.execute(select(Program).filter(Program.id == adslot.program_id))
    if not program.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")

    new_adslot = AdSlot(**adslot.model_dump())
    db.add(new_adslot)
    await db.commit()
    await db.refresh(new_adslot)
    return new_adslot
