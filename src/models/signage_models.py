from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import JSON, Enum as SAEnum
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any
import enum

class Orientation(str, enum.Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

class ContentType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    HTML = "html"
    WIDGET = "widget"

class SignageDevice(Base):
    """
    Signage Device Model
    """
    __tablename__ = "signage_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    serial: Mapped[str] = mapped_column(String, unique=True, index=True)
    # PostGIS POINT (SRID 4326)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    screen_size: Mapped[float] = mapped_column(Float) # Screen size in inches
    orientation: Mapped[Orientation] = mapped_column(SAEnum(Orientation))
    os_version: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="offline")
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    groups: Mapped[List[str]] = mapped_column(JSON, default=list) # List of group names/IDs

class ContentPlaylist(Base):
    """
    Content Playlist Model
    """
    __tablename__ = "content_playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    items: Mapped[List[Dict[str, Any]]] = mapped_column(JSON) # List of content references or embedded content
    schedule: Mapped[Dict[str, Any]] = mapped_column(JSON) # Schedule rules (e.g., cron, date range)
    loop: Mapped[bool] = mapped_column(Boolean, default=True)
    target_device_groups: Mapped[List[str]] = mapped_column(JSON) # List of target group names/IDs

class SignageContent(Base):
    """
    Signage Content Model
    """
    __tablename__ = "signage_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    content_type: Mapped[ContentType] = mapped_column(SAEnum(ContentType))
    file_uri: Mapped[str] = mapped_column(String)
    duration_sec: Mapped[int] = mapped_column(Integer)
    resolution: Mapped[str] = mapped_column(String) # e.g. "1920x1080"
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
