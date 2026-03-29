from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.quantum_models import QuantumBackend, JobStatus, AlgorithmType

class QuantumCircuitCreate(BaseModel):
    name: str
    qubit_count: int
    gate_sequence: Dict[str, Any]
    depth: int
    description: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None

class QuantumCircuitResponse(QuantumCircuitCreate):
    id: int
    creator_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SimulationJobCreate(BaseModel):
    circuit_id: int
    backend: QuantumBackend
    shots: int = 1024
    noise_model: Optional[Dict[str, Any]] = None

class SimulationJobResponse(SimulationJobCreate):
    id: int
    status: JobStatus
    result_uri: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class QuantumAlgorithmCreate(BaseModel):
    name: str
    algorithm_type: AlgorithmType
    template_circuit_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    complexity_class: Optional[str] = None

class QuantumAlgorithmResponse(QuantumAlgorithmCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)
