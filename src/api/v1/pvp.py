from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis
from pydantic import BaseModel

from src.database import get_db
from src.deps import get_redis, get_current_user_id
from src.models.pvp_models import Match, MatchMode, MatchStatus
from src.services.matchmaking_service import MatchmakingService

router = APIRouter()

class QueueRequest(BaseModel):
    mode: MatchMode

class ResultRequest(BaseModel):
    winner_id: int

async def get_matchmaking_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> MatchmakingService:
    return MatchmakingService(db, redis)

@router.post("/queue", status_code=status.HTTP_200_OK)
async def join_queue(
    req: QueueRequest,
    user_id: int = Depends(get_current_user_id),
    service: MatchmakingService = Depends(get_matchmaking_service)
):
    """
    Join the PvP queue.
    """
    await service.add_to_queue(user_id, req.mode)

    # Try to find a match immediately
    match = await service.find_match(user_id, req.mode)
    if match:
        return {"status": "matched", "match_id": match.id, "opponent_id": match.player2_id if match.player1_id == user_id else match.player1_id}

    return {"status": "queued", "message": "Added to queue, waiting for opponent."}

@router.delete("/queue", status_code=status.HTTP_204_NO_CONTENT)
async def leave_queue(
    req: QueueRequest,
    user_id: int = Depends(get_current_user_id),
    service: MatchmakingService = Depends(get_matchmaking_service)
):
    """
    Leave the PvP queue.
    """
    await service.remove_from_queue(user_id, req.mode)
    return

@router.get("/match/{match_id}")
async def get_match(
    match_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get match status.
    """
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@router.post("/match/{match_id}/result")
async def report_result(
    match_id: str,
    req: ResultRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    service: MatchmakingService = Depends(get_matchmaking_service)
):
    """
    Report match result.
    """
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.status != MatchStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Match is not active")

    if user_id not in [match.player1_id, match.player2_id]:
         raise HTTPException(status_code=403, detail="Not a participant")

    # Verify winner is part of the match
    if req.winner_id not in [match.player1_id, match.player2_id]:
        raise HTTPException(status_code=400, detail="Invalid winner_id")

    match.winner_id = req.winner_id
    match.status = MatchStatus.COMPLETED
    # Calculate duration if we had start time, assuming now is end
    # match.duration_sec = ...

    # Update Elo - this will commit the match result and rating changes transactionally
    await service.calculate_elo_change(match)

    return {"status": "completed", "winner_id": match.winner_id}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, match_id: str, websocket: WebSocket):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)

    def disconnect(self, match_id: str, websocket: WebSocket):
        if match_id in self.active_connections:
            self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]

    async def broadcast(self, match_id: str, message: str):
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{match_id}")
async def websocket_endpoint(websocket: WebSocket, match_id: str):
    await manager.connect(match_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast the received message to all connected clients in the match
            await manager.broadcast(match_id, data)
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)
        await manager.broadcast(match_id, "A player disconnected")
