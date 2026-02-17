from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base
import enum
from datetime import datetime, timezone

class OverflowAction(str, enum.Enum):
    VOICEMAIL = "voicemail"
    TRANSFER = "transfer"

class AgentStatusEnum(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    BREAK = "break"
    OFFLINE = "offline"

class ContactCenterQueue(Base):
    __tablename__ = "contact_center_queues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    max_wait_sec = Column(Integer, default=600)
    agent_ids = Column(JSON, default=list)
    overflow_action = Column(SQLEnum(OverflowAction), default=OverflowAction.VOICEMAIL)
    current_length = Column(Integer, default=0)

class AgentStatus(Base):
    __tablename__ = "agent_statuses"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, unique=True, nullable=False)
    status = Column(SQLEnum(AgentStatusEnum), default=AgentStatusEnum.OFFLINE)
    current_call_id = Column(Integer, nullable=True)
    handled_today = Column(Integer, default=0)
    avg_handle_time_sec = Column(Float, default=0.0)

class QualityScore(Base):
    __tablename__ = "quality_scores"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, nullable=False)
    supervisor_id = Column(Integer, nullable=True)
    empathy_score = Column(Float, nullable=False)
    resolution_score = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=False)
    overall = Column(Float, nullable=False)
