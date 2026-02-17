from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from src.services import search_service
from src.models import workspace_models

router = APIRouter()

# Pydantic models
class WorkspaceCreate(BaseModel):
    name: str
    slug: str
    plan: str = "free"

class WorkspaceStats(BaseModel):
    member_count: int
    storage_used_gb: float

class IntegrationConfig(BaseModel):
    service: str
    config: Dict[str, Any]
    webhooks: Optional[List[Dict[str, Any]]] = []

class MessageResponse(BaseModel):
    id: int
    content: str
    channel_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class SearchRequest(BaseModel):
    query: str
    workspace_id: int

# Endpoints
@router.post("/workspaces/create", response_model=Dict[str, Any])
async def create_workspace(workspace: WorkspaceCreate):
    # Mock implementation
    return {
        "id": 1,
        "name": workspace.name,
        "slug": workspace.slug,
        "plan": workspace.plan,
        "member_count": 0,
        "storage_used_gb": 0.0,
        "integrations": {}
    }

@router.get("/workspaces/{id}/stats", response_model=WorkspaceStats)
async def get_workspace_stats(id: int):
    # Mock implementation
    return WorkspaceStats(member_count=10, storage_used_gb=1.5)

@router.post("/workspaces/{id}/integrations")
async def add_integration(id: int, integration: IntegrationConfig):
    # Mock implementation
    if integration.service not in ["github", "jira", "google_drive", "zoom"]:
         raise HTTPException(status_code=400, detail="Invalid service")

    return {"status": "success", "integration_id": 101, "service": integration.service}

@router.get("/integrations/{id}/events")
async def get_integration_events(id: int):
    # Mock implementation
    return [{"id": 1, "type": "push", "payload": {}}]

@router.get("/threads/{id}/replies", response_model=List[MessageResponse])
async def get_thread_replies(id: int):
    # Mock implementation
    return [
        MessageResponse(id=10, content="Reply 1", channel_id=1),
        MessageResponse(id=11, content="Reply 2", channel_id=1)
    ]

@router.post("/search", response_model=List[MessageResponse])
async def search_messages(search_req: SearchRequest):
    results = await search_service.full_text_search(search_req.workspace_id, search_req.query)
    # Convert SQLAlchemy models (or mocks) to Pydantic models
    return [MessageResponse.model_validate(msg) for msg in results]
