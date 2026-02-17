from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from sqlalchemy import select

from src.database import get_db
from src.models.scouting_models import ScoutReport, TransferMarket
from src.services.scouting_service import ScoutingService

router = APIRouter()
service = ScoutingService()

# --- Schemas ---

class ScoutReportCreate(BaseModel):
    scout_id: str
    player_id: str
    skills: Dict[str, Any]
    physical_ratings: Dict[str, Any]
    recommendation: str
    market_value_estimate: float

class ScoutReportResponse(ScoutReportCreate):
    id: int
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransferRumorResponse(BaseModel):
    player_id: str
    from_club_id: str
    to_club_id: str
    fee: float
    contract_years: float
    announced_at: datetime
    transfer_type: str

    model_config = ConfigDict(from_attributes=True)

class MarketValueHistoryResponse(BaseModel):
    player_id: str
    history: List[Dict[str, Any]] # Mock history

class SimilarPlayerRequest(BaseModel):
    budget: float
    position: Optional[str] = None

class SimilarPlayerResponse(BaseModel):
    similar_players: List[Dict[str, Any]]

# --- Endpoints ---

@router.post("/scouts/reports", response_model=ScoutReportResponse, status_code=status.HTTP_201_CREATED)
async def create_scout_report(report: ScoutReportCreate, db: AsyncSession = Depends(get_db)):
    db_report = ScoutReport(**report.model_dump())
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report

@router.get("/players/{player_id}/scout-reports", response_model=List[ScoutReportResponse])
async def get_player_scout_reports(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScoutReport).where(ScoutReport.player_id == player_id))
    reports = result.scalars().all()
    return reports

@router.get("/transfer-market/rumors", response_model=List[TransferRumorResponse])
async def get_transfer_rumors(db: AsyncSession = Depends(get_db)):
    # Assuming all in TransferMarket table are 'rumors' or mock data for now
    result = await db.execute(select(TransferMarket).limit(10))
    rumors = result.scalars().all()
    return rumors

@router.get("/players/{player_id}/market-value-history", response_model=MarketValueHistoryResponse)
async def get_market_value_history(player_id: str):
    # Mock data
    return {
        "player_id": player_id,
        "history": [
            {"date": "2023-01-01", "value": 1000000.0},
            {"date": "2023-06-01", "value": 1200000.0},
            {"date": "2024-01-01", "value": 1500000.0},
        ]
    }

@router.post("/analytics/similar-players/{player_id}", response_model=SimilarPlayerResponse)
async def find_similar_players(player_id: str, request: SimilarPlayerRequest):
    similar_players = await service.find_similar_players(player_id, request.budget)
    return {"similar_players": similar_players}
