from fastapi import APIRouter, HTTPException, Query, status
from typing import List
from src.models.music_models import Podcast, Episode

router = APIRouter(prefix="/podcasts", tags=["podcasts"])
episode_router = APIRouter(prefix="/episodes", tags=["episodes"])

# Mock Data
MOCK_PODCASTS = [
    Podcast(id="p1", title="Tech Talk", host="Alice", description="Tech news", category="Technology"),
    Podcast(id="p2", title="History Hour", host="Bob", description="History lessons", category="History"),
    Podcast(id="p3", title="Comedy Club", host="Charlie", description="Funny stuff", category="Comedy"),
]

MOCK_EPISODES = [
    Episode(id="e1", podcast_id="p1", title="AI Revolution", description="About AI", duration=3600, stream_url="http://stream/e1", release_date="2023-01-01"),
    Episode(id="e2", podcast_id="p1", title="Quantum Computing", description="About QC", duration=3000, stream_url="http://stream/e2", release_date="2023-01-08"),
    Episode(id="e3", podcast_id="p2", title="Rome", description="About Rome", duration=4000, stream_url="http://stream/e3", release_date="2023-01-05"),
]

@router.get("/search", response_model=List[Podcast])
async def search_podcasts(q: str):
    """Search podcasts by query"""
    q = q.lower()
    return [p for p in MOCK_PODCASTS if q in p.title.lower() or q in p.description.lower()]

@router.get("/{id}", response_model=Podcast)
async def get_podcast(id: str):
    """Podcast details"""
    podcast = next((p for p in MOCK_PODCASTS if p.id == id), None)
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return podcast

@router.get("/{id}/episodes", response_model=List[Episode])
async def get_episodes(id: str):
    """Get episodes for a podcast"""
    return [e for e in MOCK_EPISODES if e.podcast_id == id]

@router.post("/{id}/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_podcast(id: str, user_id: str = "guest"):
    """Subscribe to a podcast"""
    podcast = next((p for p in MOCK_PODCASTS if p.id == id), None)
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    # Mock subscription logic
    return {"message": f"Subscribed to {podcast.title}"}

@episode_router.get("/{id}/stream")
async def stream_episode(id: str):
    """Stream a podcast episode"""
    episode = next((e for e in MOCK_EPISODES if e.id == id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {"stream_url": episode.stream_url}
