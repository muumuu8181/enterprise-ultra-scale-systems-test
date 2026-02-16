from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bio = Column(String)

    albums = relationship("Album", back_populates="artist", lazy="selectin")


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))

    artist = relationship("Artist", back_populates="albums", lazy="selectin")
    tracks = relationship("Track", back_populates="album", lazy="selectin")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    album_id = Column(Integer, ForeignKey("albums.id"))
    duration = Column(Integer)  # Duration in seconds
    isrc = Column(String, unique=True, index=True)

    album = relationship("Album", back_populates="tracks", lazy="selectin")
