from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import JSON
import enum
from datetime import datetime, timezone

Base = declarative_base()

class JobType(str, enum.Enum):
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"
    DATA_ANALYSIS = "data_analysis"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeStatus(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    DOWN = "down"

class ComputeJob(Base):
    __tablename__ = "compute_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    job_type = Column(SAEnum(JobType), nullable=False)
    status = Column(SAEnum(JobStatus), default=JobStatus.PENDING)
    priority = Column(Integer, default=0)
    walltime_sec = Column(Integer)
    nodes_requested = Column(Integer)
    gpus_requested = Column(Integer)
    # Use lambda to ensure time is calculated at insertion
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ComputeNode(Base):
    __tablename__ = "compute_nodes"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String, index=True)
    hostname = Column(String, unique=True)
    cpu_cores = Column(Integer)
    ram_gb = Column(Integer)
    gpu_count = Column(Integer)
    gpu_type = Column(String)
    status = Column(SAEnum(NodeStatus), default=NodeStatus.IDLE)

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    name = Column(String)
    dag_definition = Column(JSON)
    checkpointing_enabled = Column(Boolean, default=False)
    restart_count = Column(Integer, default=0)
