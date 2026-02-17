from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class TriggerType(str, Enum):
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EVENT = "event"
    MANUAL = "manual"

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class StepType(str, Enum):
    HTTP = "http"
    CODE = "code"
    CONDITION = "condition"
    DELAY = "delay"
    HUMAN_TASK = "human_task"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    trigger_type: Mapped[TriggerType] = mapped_column(SAEnum(TriggerType))
    steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)
    error_handling: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("workflow_definitions.id"))
    triggered_by: Mapped[str] = mapped_column(String(255))
    status: Mapped[WorkflowStatus] = mapped_column(SAEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    current_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("workflow_instances.id"))
    step_name: Mapped[str] = mapped_column(String(255))
    step_type: Mapped[StepType] = mapped_column(SAEnum(StepType))
    input: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    output: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    status: Mapped[StepStatus] = mapped_column(SAEnum(StepStatus), default=StepStatus.PENDING)
