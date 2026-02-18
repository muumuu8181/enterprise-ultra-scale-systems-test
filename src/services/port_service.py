from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

class BerthAssignment(BaseModel):
    berth_id: str
    assignment_time: datetime
    status: str

class SanctionsResult(BaseModel):
    vessel_id: str
    is_sanctioned: bool
    reason: Optional[str] = None

async def berth_planning(port_id: str, vessel_id: str, eta: datetime) -> BerthAssignment:
    # Placeholder logic
    # Using naive datetime.now(timezone.utc) to return a timezone-aware datetime
    return BerthAssignment(
        berth_id="B-01",
        assignment_time=datetime.now(timezone.utc),
        status="confirmed"
    )

async def check_sanctions(vessel_id: str) -> SanctionsResult:
    # Placeholder logic
    return SanctionsResult(
        vessel_id=vessel_id,
        is_sanctioned=False,
        reason=None
    )

async def calculate_port_dues(port_call_id: int) -> float:
    # Placeholder logic
    return 1000.0
