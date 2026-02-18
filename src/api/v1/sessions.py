from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from ...models.cloud_game import StreamConfig, ReconnectToken, ServerStatus, GameServer
from ...services import matchmaking

router = APIRouter()

# Request/Response Models
class StartSessionRequest(BaseModel):
    game_id: str
    player_id: str
    region: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: int
    server_id: int
    status: str
    started_at: Optional[str] = None

class SaveGameRequest(BaseModel):
    checkpoint_name: str
    save_data_uri: str
    playtime_seconds: int
    checksum: str

class SaveGameResponse(BaseModel):
    success: bool
    save_id: int

class PerformanceStatsResponse(BaseModel):
    latency_ms: int
    fps: int
    resolution: str
    packet_loss_percent: float

class GameServerResponse(BaseModel):
    id: int
    region: str
    instance_type: str
    status: ServerStatus
    current_load: float
    max_players: int

    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.post("/sessions/start", response_model=SessionResponse)
async def start_session(request: StartSessionRequest):
    # Logic to start session.
    # 1. Find optimal server
    server = await matchmaking.find_optimal_server(request.player_id, request.game_id)
    if not server:
        raise HTTPException(status_code=503, detail="No servers available")

    # 2. Create session (mocked)
    # In reality, we'd save to DB here.
    return SessionResponse(
        session_id=123,
        server_id=server.id,
        status="initializing",
        started_at="2023-10-27T10:00:00Z"
    )

@router.get("/sessions/{id}/status", response_model=SessionResponse)
async def get_session_status(id: int):
    # Mock status
    return SessionResponse(
        session_id=id,
        server_id=1,
        status="active",
        started_at="2023-10-27T10:00:00Z"
    )

@router.post("/sessions/{id}/save", response_model=SaveGameResponse)
async def save_game_session(id: int, request: SaveGameRequest):
    # Mock save
    return SaveGameResponse(success=True, save_id=456)

@router.get("/sessions/{id}/stream-url", response_model=StreamConfig)
async def get_stream_url(id: int):
    return await matchmaking.start_streaming_session(id)

@router.get("/servers/find-optimal", response_model=GameServerResponse)
async def find_optimal_server_endpoint(game_id: str, player_id: str):
    server = await matchmaking.find_optimal_server(player_id, game_id)
    return server

@router.get("/sessions/{id}/performance-stats", response_model=PerformanceStatsResponse)
async def get_performance_stats(id: int):
    # Mock stats
    return PerformanceStatsResponse(
        latency_ms=25,
        fps=60,
        resolution="1920x1080",
        packet_loss_percent=0.1
    )
