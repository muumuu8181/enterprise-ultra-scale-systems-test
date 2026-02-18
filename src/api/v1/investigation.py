from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.services import investigation_service
from src.models.investigation_aml import CaseStatus, RelationshipType

router = APIRouter(prefix="/investigation", tags=["Investigation"])

# --- Request Schemas ---

class CreateCaseRequest(BaseModel):
    sar_id: str
    analyst_id: str
    priority: int
    typology: str
    estimated_proceeds: float
    description: Optional[str] = None

class AddEntityRequest(BaseModel):
    entity1_id: str
    entity2_id: str
    relationship_type: RelationshipType
    evidence: Dict

class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str
    description: str
    actor_id: Optional[str]

class WatchlistSearchRequest(BaseModel):
    name: str
    fuzzy: bool = True

class WatchlistUploadRequest(BaseModel):
    source: str
    entries: List[Dict]

# --- Endpoints ---

@router.post("/cases/open")
async def open_case(request: CreateCaseRequest):
    # Mock logic to create a case
    # In reality, this would save to DB
    return {
        "case_id": 12345,
        "status": "open",
        "message": "Case opened successfully"
    }

@router.get("/cases/{id}/network-visualization")
async def get_network_visualization(id: int):
    # Call service
    visualization = await investigation_service.visualize_money_flow(id)
    return visualization

@router.get("/cases/{id}/timeline")
async def get_case_timeline(id: int):
    # Mock timeline logic
    return {
        "case_id": id,
        "events": [
            TimelineEvent(
                timestamp="2023-10-27T10:00:00Z",
                event_type="SAR_FILED",
                description="Suspicious Activity Report filed",
                actor_id="analyst_01"
            ),
            TimelineEvent(
                timestamp="2023-10-28T14:30:00Z",
                event_type="CASE_OPENED",
                description="Investigation case formally opened",
                actor_id="system"
            )
        ]
    }

@router.post("/cases/{id}/add-entity")
async def add_entity_to_case(id: int, request: AddEntityRequest):
    # Mock logic to add entity link
    return {
        "message": "Entity linked successfully",
        "link_id": 999
    }

@router.get("/watchlists/search")
async def search_watchlist(q: str):
    # Using 'q' as query parameter instead of body for GET request usually
    # But prompt said GET /watchlists/search, could be query params

    # Mock logic
    matches = []
    if q.lower() == "bad actor":
         matches.append({
             "match_id": "m-001",
             "name": "Bad Actor",
             "list": "OFAC",
             "score": 0.99
         })
    return {"matches": matches}

@router.post("/watchlists/upload")
async def upload_watchlist(request: WatchlistUploadRequest):
    # Mock logic
    return {
        "processed_count": len(request.entries),
        "status": "completed"
    }
