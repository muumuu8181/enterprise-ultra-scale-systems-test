from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date, timezone

router = APIRouter()

# Pydantic Models
class TrackBase(BaseModel):
    title: str
    artist_id: int
    album_id: int
    duration_sec: int
    audio_url: str

class TrackRead(TrackBase):
    id: int
    plays_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class AlbumBase(BaseModel):
    title: str
    artist_id: int
    release_date: date
    cover_url: str
    track_count: int

class AlbumRead(AlbumBase):
    id: int

    class Config:
        from_attributes = True

class PlaylistBase(BaseModel):
    user_id: int
    name: str
    tracks: List[int] # List of track IDs
    is_public: bool

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistTrackUpdate(BaseModel):
    tracks: List[int]

class PlaylistRead(PlaylistBase):
    id: int
    followers_count: int

    class Config:
        from_attributes = True

# Endpoints

@router.get("/tracks/{id}", response_model=TrackRead)
async def get_track(id: int):
    # Mock implementation
    return {
        "id": id,
        "title": "Song Title",
        "artist_id": 1,
        "album_id": 1,
        "duration_sec": 180,
        "audio_url": "http://example.com/audio.mp3",
        "plays_count": 100,
        "created_at": datetime.now(timezone.utc)
    }

@router.get("/tracks/{id}/stream")
async def stream_track(id: int):
    return {"message": "Stream url", "url": "http://example.com/stream.mp3"}

@router.get("/artists/{id}/discography", response_model=List[AlbumRead])
async def get_artist_discography(id: int):
    return [
        {
            "id": 1,
            "title": "Album 1",
            "artist_id": id,
            "release_date": date.today(),
            "cover_url": "http://example.com/cover.jpg",
            "track_count": 10
        }
    ]

@router.get("/albums/{id}/tracks", response_model=List[TrackRead])
async def get_album_tracks(id: int):
    return [
         {
            "id": 1,
            "title": "Song 1",
            "artist_id": 1,
            "album_id": id,
            "duration_sec": 180,
            "audio_url": "http://example.com/audio.mp3",
            "plays_count": 100,
            "created_at": datetime.now(timezone.utc)
        }
    ]

@router.post("/playlists", response_model=PlaylistRead)
async def create_playlist(playlist: PlaylistCreate):
    return {
        "id": 1,
        **playlist.model_dump(),
        "followers_count": 0
    }

@router.put("/playlists/{id}/tracks", response_model=PlaylistRead)
async def update_playlist_tracks(id: int, update: PlaylistTrackUpdate):
    return {
        "id": id,
        "user_id": 1,
        "name": "My Playlist",
        "tracks": update.tracks,
        "is_public": True,
        "followers_count": 5
    }
