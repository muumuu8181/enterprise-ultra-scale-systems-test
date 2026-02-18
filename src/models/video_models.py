from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from .base import Base
import enum

class VideoStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_sec = Column(Integer)
    thumbnail_url = Column(String)
    hls_url = Column(String)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    status = Column(String, default=VideoStatus.PROCESSING.value)

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    subscriber_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Playlist(Base):
    __tablename__ = 'playlists'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    videos = Column(JSON, default=[])
    is_public = Column(Boolean, default=True)

class VideoComment(Base):
    __tablename__ = 'video_comments'

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey('video_comments.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
