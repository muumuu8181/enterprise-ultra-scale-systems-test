from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.services.tournament_service import TournamentService
from src.models.tournament_models import Tournament
from datetime import datetime

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

# Schemas
class TournamentCreate(BaseModel):
    name: str
    format: str # single_elimination, double_elimination
    max_participants: int
    prize_pool: Optional[dict] = None

class TournamentResponse(BaseModel):
    id: int
    name: str
    format: str
    status: str
    max_participants: int
    prize_pool: Optional[dict] = None
    starts_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ParticipantRegister(BaseModel):
    user_id: int

class ParticipantResponse(BaseModel):
    id: int
    tournament_id: int
    user_id: int
    seed: Optional[int] = None
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MatchReport(BaseModel):
    winner_id: int
    score_a: int
    score_b: int

class MatchResponse(BaseModel):
    id: int
    tournament_id: int
    round: int
    match_number: int
    player1_id: Optional[int] = None
    player2_id: Optional[int] = None
    winner_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    score_a: Optional[int] = None
    score_b: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class StandingResponse(BaseModel):
    user_id: int
    rank: int

# Dependency
async def get_db():
    raise NotImplementedError("Database dependency must be overridden")

async def get_tournament_service(db: AsyncSession = Depends(get_db)) -> TournamentService:
    return TournamentService(db)

@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament: TournamentCreate,
    service: TournamentService = Depends(get_tournament_service)
):
    """
    トーナメントを作成する
    Create a tournament
    """
    return await service.create_tournament(
        name=tournament.name,
        format=tournament.format,
        max_participants=tournament.max_participants,
        prize_pool=tournament.prize_pool
    )

@router.post("/{id}/register", response_model=ParticipantResponse)
async def register_participant(
    id: int,
    participant: ParticipantRegister,
    service: TournamentService = Depends(get_tournament_service)
):
    """
    トーナメントに参加登録する
    Register for tournament
    """
    return await service.register_participant(tournament_id=id, user_id=participant.user_id)

@router.post("/{id}/start")
async def start_tournament(
    id: int,
    service: TournamentService = Depends(get_tournament_service)
):
    """
    トーナメントを開始する（ブラケット生成）
    Start tournament (Generate bracket)
    """
    await service.generate_bracket(tournament_id=id)
    return {"message": "Tournament started"}

@router.get("/{id}/bracket", response_model=List[MatchResponse])
async def get_bracket(
    id: int,
    service: TournamentService = Depends(get_tournament_service)
):
    """
    ブラケットを取得する
    Get bracket
    """
    return await service.get_bracket(tournament_id=id)

@router.post("/{id}/matches/{match_id}/report", response_model=MatchResponse)
async def report_match(
    id: int,
    match_id: int,
    report: MatchReport,
    service: TournamentService = Depends(get_tournament_service)
):
    """
    試合結果を報告する
    Report match result
    """
    return await service.report_match_result(
        tournament_id=id,
        match_id=match_id,
        winner_id=report.winner_id,
        score_a=report.score_a,
        score_b=report.score_b
    )

@router.get("/{id}/standings", response_model=List[StandingResponse])
async def get_standings(
    id: int,
    service: TournamentService = Depends(get_tournament_service)
):
    """
    順位表を取得する
    Get standings
    """
    return await service.calculate_standings(tournament_id=id)
