from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class Workspace(Base):
    __tablename__ = 'workspaces'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    plan = Column(String, default="free")
    member_count = Column(Integer, default=0)
    storage_used_gb = Column(Float, default=0.0)
    integrations = Column(JSON, default={})

    # Relationships
    workspace_integrations = relationship("WorkspaceIntegration", back_populates="workspace")


class WorkspaceIntegration(Base):
    __tablename__ = 'workspace_integrations'

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False)
    service = Column(String, nullable=False) # Enum: github, jira, google_drive, zoom
    config = Column(JSON, default={})
    webhooks = Column(JSON, default=[])

    workspace = relationship("Workspace", back_populates="workspace_integrations")


class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=True) # Assuming channels belong to workspace


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Thread(Base):
    __tablename__ = 'threads'

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    parent_message_id = Column(Integer, ForeignKey('messages.id'), nullable=False)
    reply_count = Column(Integer, default=0)
    last_reply_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    participants = Column(JSON, default=[])

    channel = relationship("Channel")
    parent_message = relationship("Message")
