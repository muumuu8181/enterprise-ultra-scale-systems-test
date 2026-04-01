from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.models.broadcast_models import ChannelType, ChannelStatus, ProgramRating, ProgramStatus, AdSlotPosition, AdSlotStatus

class ChannelBase(BaseModel):
    name: str
    channel_type: ChannelType
    frequency: Optional[str] = None
    region: Optional[str] = None
    owner_id: Optional[int] = None
    status: ChannelStatus = ChannelStatus.ACTIVE

class ChannelCreate(ChannelBase):
    pass

class ChannelResponse(ChannelBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ProgramBase(BaseModel):
    title: str
    genre: Optional[str] = None
    duration_min: int
    rating: Optional[ProgramRating] = None
    scheduled_at: datetime
    status: ProgramStatus = ProgramStatus.SCHEDULED

class ProgramCreate(ProgramBase):
    channel_id: int

class ProgramResponse(ProgramBase):
    id: int
    channel_id: int
    model_config = ConfigDict(from_attributes=True)

class AdSlotBase(BaseModel):
    position: AdSlotPosition
    duration_sec: int
    price: float
    advertiser_id: Optional[int] = None
    creative_url: Optional[str] = None
    impressions: int = 0
    status: AdSlotStatus = AdSlotStatus.AVAILABLE

class AdSlotCreate(AdSlotBase):
    program_id: int

class AdSlotResponse(AdSlotBase):
    id: int
    program_id: int
    model_config = ConfigDict(from_attributes=True)

class AdSlotBookRequest(BaseModel):
    adslot_id: int
    advertiser_id: int
    creative_url: str

class AnalyticsViewership(BaseModel):
    program_id: int
    viewers: int
    peak_viewers: int
    avg_watch_time_min: float

class AnalyticsAdPerformance(BaseModel):
    ad_slot_id: int
    impressions: int
    clicks: int
    ctr: float
