from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from src.services.music_recommender import MusicRecommender, MOCK_TRACKS
from src.models.music_models import Track, Genre

router = APIRouter(prefix="/discovery", tags=["discovery"])

def get_recommender():
    return MusicRecommender()

@router.get("/for-you", response_model=List[Track])
async def for_you(user_id: str = "guest", recommender: MusicRecommender = Depends(get_recommender)):
    """Personalized recommendations"""
    return recommender.collaborative_filtering(user_id)

@router.get("/new-releases", response_model=List[Track])
async def new_releases():
    """New releases"""
    # Mock: return recent tracks. For now, just all tracks sorted by something
    return sorted(MOCK_TRACKS, key=lambda x: x.release_date, reverse=True)

@router.get("/charts", response_model=List[Track])
async def charts(genre: Optional[Genre] = None):
    """Charts, optionally filtered by genre"""
    tracks = MOCK_TRACKS
    if genre:
        tracks = [t for t in tracks if t.genre == genre]
    # Mock: sorted by popularity (using energy as proxy for now)
    return sorted(tracks, key=lambda x: x.energy, reverse=True)

@router.get("/radio/{seed_track_id}", response_model=List[Track])
async def radio(seed_track_id: str, recommender: MusicRecommender = Depends(get_recommender)):
    """Radio station based on a seed track"""
    queue = recommender.generate_radio_queue(seed_track_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Seed track not found")
    return queue
