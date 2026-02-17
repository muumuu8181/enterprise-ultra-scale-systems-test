from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import enum
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

class ServerStatus(str, enum.Enum):
    AVAILABLE = "available"
    RUNNING = "running"
    DRAINING = "draining"

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, index=True)
    player_id = Column(String, index=True)
    server_region = Column(String)
    instance_id = Column(String)
    latency_ms = Column(Integer, nullable=True)
    fps = Column(Integer, nullable=True)
    resolution = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())

class GameServer(Base):
    __tablename__ = "game_servers"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String)
    instance_type = Column(String)
    status = Column(Enum(ServerStatus), default=ServerStatus.AVAILABLE)
    current_load = Column(Float, default=0.0)
    max_players = Column(Integer, default=100)

class SaveGame(Base):
    __tablename__ = "save_games"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String, index=True)
    game_id = Column(String, index=True)
    checkpoint_name = Column(String)
    save_data_uri = Column(String)
    playtime_seconds = Column(Integer)
    checksum = Column(String)

# Pydantic models for service return types
class StreamConfig(BaseModel):
    stream_url: str
    protocol: str
    bitrate_kbps: int

class ReconnectToken(BaseModel):
    token: str
    expires_in_seconds: int
