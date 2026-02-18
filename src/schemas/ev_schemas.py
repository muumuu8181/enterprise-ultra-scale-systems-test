from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChargingProfile(BaseModel):
    charger_id: int
    schedule: List[Dict[str, Any]] # e.g. [{"time": "10:00", "limit_kw": 22.0}]

class FleetChargePlan(BaseModel):
    site_id: int
    vehicle_schedules: Dict[int, ChargingProfile]
    total_cost_estimate: float
