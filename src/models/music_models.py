from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID, uuid4

class Genre(str, Enum):
    POP = "pop"
    ROCK = "rock"
    JAZZ = "jazz"
    CLASSICAL = "classical"
    HIP_HOP = "hip_hop"
    ELECTRONIC = "electronic"
    OTHER = "other"

class Track(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    artist: str
    album: str
    genre: Genre
    duration: int  # in seconds
    bpm: int
    key: str
    energy: float # 0.0 to 1.0
    release_date: str

class Podcast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    host: str
    description: str
    category: str

class Episode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    podcast_id: str
    title: str
    description: str
    duration: int
    stream_url: str
    release_date: str

class UserTasteProfile(BaseModel):
    favorite_genres: List[Genre] = []
    favorite_artists: List[str] = []

class User(BaseModel):
    id: str
    username: str
    taste_profile: UserTasteProfile
