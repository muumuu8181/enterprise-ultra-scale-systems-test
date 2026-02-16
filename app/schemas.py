from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Track Schemas
class TrackBase(BaseModel):
    title: str
    duration: int
    isrc: str

class TrackCreate(TrackBase):
    album_id: int

class Track(TrackBase):
    id: int
    album_id: int

    model_config = ConfigDict(from_attributes=True)


# Album Schemas
class AlbumBase(BaseModel):
    title: str

class AlbumCreate(AlbumBase):
    artist_id: int

class Album(AlbumBase):
    id: int
    artist_id: int
    tracks: List[Track] = []

    model_config = ConfigDict(from_attributes=True)


# Artist Schemas
class ArtistBase(BaseModel):
    name: str
    bio: Optional[str] = None

class ArtistCreate(ArtistBase):
    pass

class Artist(ArtistBase):
    id: int
    albums: List[Album] = []

    model_config = ConfigDict(from_attributes=True)
