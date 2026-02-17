from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from src.core.database import Base
from datetime import datetime
import enum

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    subject = Column(String)
    description = Column(String)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    sla_due_at = Column(DateTime, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    agent = relationship("Agent", back_populates="tickets")
    csat = relationship("CSATScore", back_populates="ticket", uselist=False)

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    status = Column(String, default="available")

    tickets = relationship("Ticket", back_populates="agent")

class CSATScore(Base):
    __tablename__ = "csat_scores"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    score = Column(Integer) # 1-5
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="csat")
