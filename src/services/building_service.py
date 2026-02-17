from pydantic import BaseModel
from typing import List, Dict, Optional
import random
import asyncio

class HVACSchedule(BaseModel):
    building_id: int
    schedule: Dict[str, List[float]]  # zone_id -> [temps over time]
    optimized_savings: float

class EvacuationRoute(BaseModel):
    floor_number: int
    route_description: str
    estimated_time_minutes: float

class EvacuationPlan(BaseModel):
    building_id: int
    emergency_type: str
    routes: List[EvacuationRoute]
    assembly_points: List[str]

async def optimize_hvac(building_id: int, comfort_weight: float = 0.7) -> HVACSchedule:
    """
    Optimizes HVAC settings for energy efficiency vs comfort.
    """
    # Simulate processing time
    await asyncio.sleep(0.1)

    # Mock logic
    return HVACSchedule(
        building_id=building_id,
        schedule={
            "zone_1": [22.0, 21.5, 21.0, 20.5],
            "zone_2": [23.0, 22.5, 22.0, 21.5]
        },
        optimized_savings=15.5 * comfort_weight
    )

async def predict_energy_consumption(building_id: int, hours: int = 24) -> List[float]:
    """
    Predicts energy consumption for the next N hours.
    """
    await asyncio.sleep(0.1)
    # Mock logic: random consumption data
    return [round(random.uniform(5.0, 15.0), 2) for _ in range(hours)]

async def simulate_evacuation(building_id: int, emergency_type: str) -> EvacuationPlan:
    """
    Generates an evacuation plan based on emergency type.
    """
    await asyncio.sleep(0.1)
    # Mock logic
    return EvacuationPlan(
        building_id=building_id,
        emergency_type=emergency_type,
        routes=[
            EvacuationRoute(floor_number=1, route_description="Use main exit", estimated_time_minutes=2.5),
            EvacuationRoute(floor_number=2, route_description="Use stairwell A", estimated_time_minutes=4.0)
        ],
        assembly_points=["North Parking Lot", "Main Park"]
    )
