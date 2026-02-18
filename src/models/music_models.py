from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bio = Column(String)
    genres = Column(JSON)
    monthly_listeners = Column(Integer, default=0)
    verified = Column(Boolean, default=False)

    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", back_populates="artist")


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    release_date = Column(Date)
    cover_url = Column(String)
    track_count = Column(Integer, default=0)

    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    album_id = Column(Integer, ForeignKey("albums.id"))
    duration_sec = Column(Integer)
    audio_url = Column(String)
    plays_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String)
    tracks = Column(JSON)
    is_public = Column(Boolean, default=True)
    followers_count = Column(Integer, default=0)


class UserListeningHistory(Base):
    __tablename__ = "user_listening_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    duration_played_sec = Column(Integer)

    track = relationship("Track")
