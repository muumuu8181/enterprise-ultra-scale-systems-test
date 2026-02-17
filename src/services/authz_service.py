from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class Permission(BaseModel):
    resource: str
    action: str
    effect: str = "allow"

class RiskSignal(BaseModel):
    identity_id: int
    risk_score: float
    severity: str # e.g. "low", "medium", "high", "critical"
    details: Dict[str, Any]
    timestamp: datetime

async def evaluate_policy(principal_id: int, resource: str, action: str) -> bool:
    """
    Evaluates if the principal has permission to perform the action on the resource.
    This is a simplified implementation.
    """
    # In a real implementation, this would:
    # 1. Fetch the identity and its roles.
    # 2. Fetch resource policies for the specific resource.
    # 3. Evaluate the policies against the request.

    # Mock logic: deny if principal_id is 0, else allow
    if principal_id == 0:
        return False
    return True

async def compute_effective_permissions(identity_id: int) -> List[Permission]:
    """
    Computes the effective permissions for an identity based on roles and policies.
    """
    # Mock logic: return a default set of permissions
    return [
        Permission(resource="*", action="read", effect="allow"),
        Permission(resource="profile", action="update", effect="allow")
    ]

async def detect_anomalous_access(identity_id: int, access_event: Dict[str, Any]) -> RiskSignal:
    """
    Detects if an access event is anomalous.
    """
    # Mock logic: high risk if IP is from a specific block (simulated)
    is_risky = access_event.get("ip_address", "").startswith("192.168.0.")

    score = 0.8 if is_risky else 0.1
    severity = "high" if is_risky else "low"

    return RiskSignal(
        identity_id=identity_id,
        risk_score=score,
        severity=severity,
        details={"event": access_event},
        timestamp=datetime.now()
    )
