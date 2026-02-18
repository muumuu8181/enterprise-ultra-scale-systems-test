from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.twin_models import DigitalTwin, TwinState, TwinSimulation
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Any, Optional

class TwinService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_twin(self, physical_asset_id: str, asset_type: str, model_uri: str, sync_interval_sec: int = 60) -> DigitalTwin:
        twin = DigitalTwin(
            physical_asset_id=physical_asset_id,
            asset_type=asset_type,
            model_uri=model_uri,
            sync_interval_sec=sync_interval_sec
        )
        self.db.add(twin)
        await self.db.commit()
        await self.db.refresh(twin)
        return twin

    async def get_twin(self, twin_id: int) -> Optional[DigitalTwin]:
        stmt = select(DigitalTwin).where(DigitalTwin.id == twin_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def sync_physical_to_digital(self, twin_id: int, sensor_data: Dict[str, Any]) -> TwinState:
        stmt = select(DigitalTwin).where(DigitalTwin.id == twin_id)
        result = await self.db.execute(stmt)
        twin = result.scalar_one_or_none()

        if not twin:
            raise ValueError(f"Twin {twin_id} not found")

        state = TwinState(
            twin_id=twin_id,
            timestamp=datetime.utcnow(),
            state_data=sensor_data,
            simulation_mode="real"
        )
        self.db.add(state)

        twin.last_sync = datetime.utcnow()
        self.db.add(twin)

        await self.db.commit()
        await self.db.refresh(state)
        return state

    async def get_current_state(self, twin_id: int) -> Optional[TwinState]:
        stmt = select(TwinState).where(TwinState.twin_id == twin_id).order_by(TwinState.timestamp.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(self, twin_id: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[TwinState]:
        stmt = select(TwinState).where(TwinState.twin_id == twin_id)
        if from_date:
            stmt = stmt.where(TwinState.timestamp >= from_date)
        if to_date:
            stmt = stmt.where(TwinState.timestamp <= to_date)
        stmt = stmt.order_by(TwinState.timestamp.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_simulation(self, twin_id: int, scenario_name: str, parameters: Dict[str, Any]) -> TwinSimulation:
        sim = TwinSimulation(
            twin_id=twin_id,
            scenario_name=scenario_name,
            parameters=parameters,
            status="queued"
        )
        self.db.add(sim)
        await self.db.commit()
        await self.db.refresh(sim)
        return sim

    async def get_simulation(self, simulation_id: int) -> Optional[TwinSimulation]:
        stmt = select(TwinSimulation).where(TwinSimulation.id == simulation_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def run_simulation(self, sim: TwinSimulation):
        # Ensure the object is attached to the current session if it was detached
        if sim not in self.db:
             sim = await self.db.merge(sim)

        sim.status = "running"
        await self.db.commit()

        # Simulate computation time
        await asyncio.sleep(0.1)

        sim.status = "completed"
        sim.result_uri = f"s3://bucket/simulations/{sim.id}/results.json"
        await self.db.commit()
        return sim

    async def detect_anomaly(self, twin_id: int) -> List[Dict[str, Any]]:
        state = await self.get_current_state(twin_id)
        anomalies = []
        if state and state.state_data:
            data = state.state_data
            # Mock check: temperature > 100
            temp = data.get("temperature")
            if temp and isinstance(temp, (int, float)) and temp > 100:
                anomalies.append({
                    "id": "ANOMALY-001",
                    "type": "high_temperature",
                    "severity": "high",
                    "description": f"Temperature {temp} exceeds threshold 100"
                })
        return anomalies

    async def predict_future_state(self, twin_id: int, horizon_min: int) -> TwinState:
        state = await self.get_current_state(twin_id)
        if not state:
            raise ValueError(f"No state found for twin {twin_id}")

        current_data = state.state_data or {}

        future_data = current_data.copy()

        # Increment numeric values slightly to simulate trend
        for k, v in future_data.items():
            if isinstance(v, (int, float)):
                future_data[k] = v * 1.05

        predicted_time = datetime.utcnow() + timedelta(minutes=horizon_min)

        return TwinState(
            twin_id=twin_id,
            timestamp=predicted_time,
            state_data=future_data,
            simulation_mode="predicted"
        )
