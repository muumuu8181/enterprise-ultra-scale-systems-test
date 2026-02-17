from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.db.session import get_db
from src.models.security_models import (
    ThreatIndicator, SecurityEvent, Vulnerability, Campaign,
    SeverityLevel, IOCType, TLPMarking, VulnStatus
)
from src.services.threat_intel import enrich_ioc, correlate_events

router = APIRouter()

# --- Pydantic Schemas ---

class ThreatIndicatorBase(BaseModel):
    ioc_type: IOCType
    value: str
    severity: SeverityLevel
    confidence: float
    tlp_marking: Optional[TLPMarking] = None

class ThreatIndicatorCreate(ThreatIndicatorBase):
    pass

class ThreatIndicatorRead(ThreatIndicatorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class SecurityEventBase(BaseModel):
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    event_type: str
    severity: SeverityLevel
    raw_log: Optional[str] = None
    mitre_technique_id: Optional[str] = None

class SecurityEventCreate(SecurityEventBase):
    pass

class SecurityEventRead(SecurityEventBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class CampaignRead(BaseModel):
    id: int
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DashboardSummary(BaseModel):
    total_indicators: int
    high_severity_indicators: int
    total_events: int
    active_campaigns: int

# --- Endpoints ---

@router.post("/indicators", response_model=List[ThreatIndicatorRead])
async def create_indicators(
    indicators: List[ThreatIndicatorCreate],
    db: AsyncSession = Depends(get_db)
):
    new_indicators = []
    for ind in indicators:
        # Enriched mock
        enrichment = await enrich_ioc(ind.value, ind.ioc_type)
        # Use enrichment data if needed, for now just create
        db_ind = ThreatIndicator(**ind.model_dump())
        db.add(db_ind)
        new_indicators.append(db_ind)

    await db.commit()
    for ind in new_indicators:
        await db.refresh(ind)

    return new_indicators

@router.get("/indicators", response_model=List[ThreatIndicatorRead])
async def get_indicators(
    severity: Optional[SeverityLevel] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ThreatIndicator)
    if severity:
        stmt = stmt.where(ThreatIndicator.severity == severity)

    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/correlate", response_model=List[CampaignRead])
async def correlate_events_endpoint(
    events: List[SecurityEventCreate],
    db: AsyncSession = Depends(get_db)
):
    # Convert Pydantic models to ORM models (not persisted yet) for service logic
    orm_events = [SecurityEvent(**evt.model_dump()) for evt in events]

    campaigns = await correlate_events(orm_events)

    # Persist campaigns if they are new (service returns new instances)
    for camp in campaigns:
        db.add(camp)

    await db.commit()
    for camp in campaigns:
        await db.refresh(camp)

    return campaigns

@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    # Count indicators
    stmt_ind = select(func.count(ThreatIndicator.id))
    total_ind = (await db.execute(stmt_ind)).scalar() or 0

    stmt_high = select(func.count(ThreatIndicator.id)).where(ThreatIndicator.severity == SeverityLevel.HIGH)
    high_ind = (await db.execute(stmt_high)).scalar() or 0

    # Count events
    stmt_evt = select(func.count(SecurityEvent.id))
    total_evt = (await db.execute(stmt_evt)).scalar() or 0

    # Count campaigns
    stmt_camp = select(func.count(Campaign.id))
    total_camp = (await db.execute(stmt_camp)).scalar() or 0

    return DashboardSummary(
        total_indicators=total_ind,
        high_severity_indicators=high_ind,
        total_events=total_evt,
        active_campaigns=total_camp
    )
