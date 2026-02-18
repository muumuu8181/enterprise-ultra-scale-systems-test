from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from src.services import building_service

router = APIRouter()

@router.get("/buildings/{id}/energy-dashboard")
async def get_energy_dashboard(id: int):
    """
    Get the energy dashboard for a specific building.
    """
    consumption = await building_service.predict_energy_consumption(id, hours=24)
    return {
        "building_id": id,
        "current_usage_kwh": 125.5,
        "daily_total_kwh": sum(consumption),
        "predicted_24h": consumption
    }

@router.post("/buildings/{id}/hvac-optimize")
async def optimize_hvac(id: int, comfort_weight: float = Body(0.7, embed=True)):
    """
    Optimize HVAC settings based on comfort weight.
    """
    return await building_service.optimize_hvac(id, comfort_weight)

@router.get("/buildings/{id}/occupancy-heatmap")
async def get_occupancy_heatmap(id: int):
    """
    Get current occupancy heatmap.
    """
    return {
        "building_id": id,
        "heatmap": {
            "floor_1": {"zone_A": "high", "zone_B": "low"},
            "floor_2": {"zone_A": "medium", "zone_B": "empty"}
        }
    }

@router.post("/buildings/{id}/emergency-mode")
async def activate_emergency_mode(id: int, emergency_type: str = Body(..., embed=True)):
    """
    Activate emergency mode and get evacuation plan.
    """
    return await building_service.simulate_evacuation(id, emergency_type)

@router.get("/buildings/{id}/carbon-footprint")
async def get_carbon_footprint(id: int):
    """
    Get carbon footprint metrics.
    """
    return {
        "building_id": id,
        "co2_emissions_kg_today": 450.2,
        "sustainability_rating": "A"
    }

@router.post("/buildings/{id}/schedule-maintenance")
async def schedule_maintenance(id: int, date: str = Body(..., embed=True), description: str = Body(..., embed=True)):
    """
    Schedule maintenance for the building.
    """
    return {
        "building_id": id,
        "status": "scheduled",
        "maintenance_id": 12345,
        "date": date,
        "description": description
    }
