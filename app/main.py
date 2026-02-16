from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from . import models, schemas
from .database import engine, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Music Streaming Platform API"}

# Artist Endpoints
@app.post("/artists/", response_model=schemas.Artist)
async def create_artist(artist: schemas.ArtistCreate, db: AsyncSession = Depends(get_db)):
    db_artist = models.Artist(name=artist.name, bio=artist.bio)
    db.add(db_artist)
    await db.commit()
    await db.refresh(db_artist)
    return db_artist

@app.get("/artists/{artist_id}", response_model=schemas.Artist)
async def read_artist(artist_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Artist).filter(models.Artist.id == artist_id))
    db_artist = result.scalars().first()
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist

@app.get("/artists/", response_model=List[schemas.Artist])
async def read_artists(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Artist).offset(skip).limit(limit))
    artists = result.scalars().all()
    return artists

# Album Endpoints
@app.post("/albums/", response_model=schemas.Album)
async def create_album(album: schemas.AlbumCreate, db: AsyncSession = Depends(get_db)):
    # Check if artist exists
    result = await db.execute(select(models.Artist).filter(models.Artist.id == album.artist_id))
    artist = result.scalars().first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    db_album = models.Album(**album.model_dump())
    db.add(db_album)
    await db.commit()
    await db.refresh(db_album)
    return db_album

@app.get("/albums/{album_id}", response_model=schemas.Album)
async def read_album(album_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Album).filter(models.Album.id == album_id))
    db_album = result.scalars().first()
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

@app.get("/albums/", response_model=List[schemas.Album])
async def read_albums(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Album).offset(skip).limit(limit))
    albums = result.scalars().all()
    return albums

# Track Endpoints
@app.post("/tracks/", response_model=schemas.Track)
async def create_track(track: schemas.TrackCreate, db: AsyncSession = Depends(get_db)):
    # Check if album exists
    result = await db.execute(select(models.Album).filter(models.Album.id == track.album_id))
    album = result.scalars().first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    db_track = models.Track(**track.model_dump())
    db.add(db_track)
    await db.commit()
    await db.refresh(db_track)
    return db_track

@app.get("/tracks/{track_id}", response_model=schemas.Track)
async def read_track(track_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Track).filter(models.Track.id == track_id))
    db_track = result.scalars().first()
    if db_track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return db_track

@app.get("/tracks/", response_model=List[schemas.Track])
async def read_tracks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Track).offset(skip).limit(limit))
    tracks = result.scalars().all()
    return tracks
