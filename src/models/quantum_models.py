from typing import Optional, Any
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from src.database import Base

class QuantumBackend(str, Enum):
    STATEVECTOR = "statevector"
    DENSITY_MATRIX = "density_matrix"
    MPS = "mps"

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AlgorithmType(str, Enum):
    GROVER = "grover"
    SHOR = "shor"
    VQE = "vqe"
    QAOA = "qaoa"

class QuantumCircuit(Base):
    __tablename__ = "quantum_circuits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    qubit_count: Mapped[int] = mapped_column(Integer)
    gate_sequence: Mapped[dict[str, Any]] = mapped_column(JSON)
    depth: Mapped[int] = mapped_column(Integer)
    creator_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    simulations: Mapped[list["SimulationJob"]] = relationship("SimulationJob", back_populates="circuit")
    algorithms: Mapped[list["QuantumAlgorithm"]] = relationship("QuantumAlgorithm", back_populates="template_circuit")

class SimulationJob(Base):
    __tablename__ = "simulation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    circuit_id: Mapped[int] = mapped_column(Integer, ForeignKey("quantum_circuits.id"))
    backend: Mapped[QuantumBackend] = mapped_column(SAEnum(QuantumBackend))
    shots: Mapped[int] = mapped_column(Integer)
    noise_model: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.QUEUED)
    result_uri: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    circuit: Mapped["QuantumCircuit"] = relationship("QuantumCircuit", back_populates="simulations")

class QuantumAlgorithm(Base):
    __tablename__ = "quantum_algorithms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    algorithm_type: Mapped[AlgorithmType] = mapped_column(SAEnum(AlgorithmType))
    template_circuit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("quantum_circuits.id"), nullable=True)
    parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    complexity_class: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    template_circuit: Mapped[Optional["QuantumCircuit"]] = relationship("QuantumCircuit", back_populates="algorithms")
