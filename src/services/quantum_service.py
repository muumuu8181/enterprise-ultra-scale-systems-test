from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.quantum_models import QuantumCircuit, SimulationJob, QuantumAlgorithm, JobStatus
from src.schemas.quantum_schemas import QuantumCircuitCreate, SimulationJobCreate, QuantumAlgorithmCreate
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class QuantumService:
    async def create_circuit(self, db: AsyncSession, circuit_in: QuantumCircuitCreate, creator_id: str) -> QuantumCircuit:
        circuit = QuantumCircuit(
            **circuit_in.model_dump(),
            creator_id=creator_id
        )
        db.add(circuit)
        await db.commit()
        await db.refresh(circuit)
        return circuit

    async def get_circuit(self, db: AsyncSession, circuit_id: int) -> Optional[QuantumCircuit]:
        return await db.get(QuantumCircuit, circuit_id)

    async def create_simulation_job(self, db: AsyncSession, job_in: SimulationJobCreate) -> SimulationJob:
        # Verify circuit exists
        circuit = await self.get_circuit(db, job_in.circuit_id)
        if not circuit:
            raise ValueError(f"Circuit {job_in.circuit_id} not found")

        job = SimulationJob(
            **job_in.model_dump(),
            status=JobStatus.QUEUED,
            started_at=datetime.now(timezone.utc)
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        # Mock execution logic: immediately complete
        # In real life, this would be picked up by Celery
        job.status = JobStatus.COMPLETED
        job.result_uri = f"s3://results/{job.id}.json"
        job.completed_at = datetime.now(timezone.utc)
        job.execution_time_ms = 150 # Mock time
        await db.commit()
        await db.refresh(job)

        return job

    async def get_simulation_job(self, db: AsyncSession, job_id: int) -> Optional[SimulationJob]:
        return await db.get(SimulationJob, job_id)

    async def list_algorithms(self, db: AsyncSession, type_filter: Optional[str] = None) -> List[QuantumAlgorithm]:
        query = select(QuantumAlgorithm)
        if type_filter:
            query = query.where(QuantumAlgorithm.algorithm_type == type_filter)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_algorithm(self, db: AsyncSession, algo_in: QuantumAlgorithmCreate) -> QuantumAlgorithm:
        algo = QuantumAlgorithm(**algo_in.model_dump())
        db.add(algo)
        await db.commit()
        await db.refresh(algo)
        return algo

    async def instantiate_algorithm(self, db: AsyncSession, algo_id: int, creator_id: str) -> QuantumCircuit:
        algo = await db.get(QuantumAlgorithm, algo_id)
        if not algo:
            raise ValueError(f"Algorithm {algo_id} not found")

        # Mock logic: Create a new circuit based on the algorithm template
        if algo.template_circuit_id:
            template = await self.get_circuit(db, algo.template_circuit_id)
            if not template:
                # Fallback if template missing
                new_circuit = QuantumCircuit(
                    name=f"{algo.name} Instance",
                    qubit_count=4,
                    gate_sequence={},
                    depth=1,
                    creator_id=creator_id,
                    description=f"Instantiated from {algo.name} (Template Missing)",
                    tags={"source_algorithm": algo.name}
                )
            else:
                new_circuit = QuantumCircuit(
                    name=f"{algo.name} Instance",
                    qubit_count=template.qubit_count,
                    gate_sequence=template.gate_sequence,
                    depth=template.depth,
                    creator_id=creator_id,
                    description=f"Instantiated from {algo.name}",
                    tags={"source_algorithm": algo.name}
                )
        else:
            # Create a dummy circuit if no template
            new_circuit = QuantumCircuit(
                name=f"{algo.name} Instance",
                qubit_count=2,
                gate_sequence={},
                depth=1,
                creator_id=creator_id,
                description=f"Instantiated from {algo.name}",
                tags={"source_algorithm": algo.name}
            )

        db.add(new_circuit)
        await db.commit()
        await db.refresh(new_circuit)
        return new_circuit

quantum_service = QuantumService()
