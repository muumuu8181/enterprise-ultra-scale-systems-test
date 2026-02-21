from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, ConfigDict

from src.database import get_db
from src.models.tournament_models import Tournament, Match, Team, TournamentFormat, TournamentStatus, MatchStatus

router = APIRouter()

# --- Schemas ---

class TournamentCreate(BaseModel):
    game_id: str
    name: str
    format: TournamentFormat
    max_participants: int
    entry_fee: float
    prize_pool: float
    start_date: datetime

class TournamentResponse(TournamentCreate):
    id: int
    status: TournamentStatus
    model_config = ConfigDict(from_attributes=True)

class TeamCreate(BaseModel):
    name: str
    captain_id: int
    members: List[dict] # JSON
    region: str

class TeamResponse(TeamCreate):
    id: int
    elo_rating: int
    wins: int
    losses: int
    tournament_history: List[dict]
    model_config = ConfigDict(from_attributes=True)

class MatchResponse(BaseModel):
    id: int
    tournament_id: int
    round_number: int
    team_a_id: Optional[int]
    team_b_id: Optional[int]
    score_a: int
    score_b: int
    winner_id: Optional[int]
    scheduled_at: datetime
    stream_url: Optional[str]
    status: MatchStatus
    model_config = ConfigDict(from_attributes=True)

class MatchResultReport(BaseModel):
    score_a: int
    score_b: int
    winner_id: int

class LeaderboardEntry(BaseModel):
    team_id: int
    team_name: str
    elo_rating: int
    wins: int
    losses: int

class ViewerStatsResponse(BaseModel):
    tournament_id: int
    concurrent_viewers: int # Mocked

class TeamRegisterRequest(BaseModel):
    team_id: int

# --- Endpoints ---

@router.get("/tournaments", response_model=List[TournamentResponse])
async def list_tournaments(
    game: Optional[str] = Query(None),
    status: Optional[TournamentStatus] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Tournament)
    if game:
        query = query.where(Tournament.game_id == game)
    if status:
        query = query.where(Tournament.status == status)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/tournaments/create", response_model=TournamentResponse)
async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    db_tournament = Tournament(**tournament.model_dump())
    db.add(db_tournament)
    await db.commit()
    await db.refresh(db_tournament)
    return db_tournament

@router.post("/tournaments/{id}/register")
async def register_team(id: int, request: TeamRegisterRequest, db: AsyncSession = Depends(get_db)):
    tournament = await db.get(Tournament, id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    team = await db.get(Team, request.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if tournament.status != TournamentStatus.registration:
        raise HTTPException(status_code=400, detail="Tournament is not open for registration")

    current_participants = list(tournament.participants) if tournament.participants else []
    if len(current_participants) >= tournament.max_participants:
        raise HTTPException(status_code=400, detail="Tournament is full")

    if request.team_id in current_participants:
        raise HTTPException(status_code=400, detail="Team already registered")

    # Update tournament participants
    current_participants.append(request.team_id)
    tournament.participants = current_participants

    # Update team history
    history = list(team.tournament_history) if team.tournament_history else []
    history.append({
        "tournament_id": id,
        "tournament_name": tournament.name,
        "registered_at": datetime.now().isoformat()
    })
    team.tournament_history = history

    db.add(tournament)
    db.add(team)
    await db.commit()

    return {"message": "Team registered"}

@router.get("/tournaments/{id}/bracket", response_model=List[MatchResponse])
async def get_bracket(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.tournament_id == id).order_by(Match.round_number))
    return result.scalars().all()

@router.post("/matches/{id}/report-result", response_model=MatchResponse)
async def report_match_result(id: int, report: MatchResultReport, db: AsyncSession = Depends(get_db)):
    match = await db.get(Match, id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.score_a = report.score_a
    match.score_b = report.score_b
    match.winner_id = report.winner_id
    match.status = MatchStatus.completed

    await db.commit()
    await db.refresh(match)
    return match

@router.get("/matches/{id}/live-stats")
async def get_live_stats(id: int):
    # Mock data
    return {"match_id": id, "viewers": 1200, "current_gold_diff": 500}

@router.get("/teams/{id}/profile", response_model=TeamResponse)
async def get_team_profile(id: int, db: AsyncSession = Depends(get_db)):
    team = await db.get(Team, id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    game: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    # Ignoring game for team model since team doesn't have game_id (assuming multi-game team or just global elo)
    # But filtering by region
    query = select(Team).order_by(desc(Team.elo_rating))
    if region:
        query = query.where(Team.region == region)

    result = await db.execute(query)
    teams = result.scalars().all()

    return [
        LeaderboardEntry(
            team_id=t.id,
            team_name=t.name,
            elo_rating=t.elo_rating,
            wins=t.wins,
            losses=t.losses
        ) for t in teams
    ]

@router.get("/analytics/viewer-stats/{tournament_id}", response_model=ViewerStatsResponse)
async def get_viewer_stats(tournament_id: int):
    # Mock data
    return ViewerStatsResponse(tournament_id=tournament_id, concurrent_viewers=5000)
