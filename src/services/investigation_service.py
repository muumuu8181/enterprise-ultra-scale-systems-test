from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

# --- Return Types (Schemas) ---

class NetworkNode(BaseModel):
    id: str
    label: str
    type: str  # e.g., "account", "company", "person"

class NetworkEdge(BaseModel):
    source: str
    target: str
    relationship: str
    weight: float = 1.0

class NetworkVisualization(BaseModel):
    case_id: int
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class RiskExposure(BaseModel):
    entity_id: str
    risk_score: float  # 0.0 to 100.0
    risk_level: str  # "Low", "Medium", "High", "Critical"
    factors: List[str]

class WatchlistMatch(BaseModel):
    match_id: str
    watchlist_id: int
    confidence_score: float
    matched_name: str
    list_type: str

# --- Service Logic ---

async def visualize_money_flow(case_id: int) -> NetworkVisualization:
    """
    Generates a network visualization for a given AML case.
    This is a mock implementation.
    """
    # In a real implementation, this would query the graph database or entity links
    nodes = [
        NetworkNode(id="entity_A", label="Company A", type="company"),
        NetworkNode(id="entity_B", label="Person B", type="person"),
        NetworkNode(id="account_C", label="Account 123", type="account"),
    ]
    edges = [
        NetworkEdge(source="entity_B", target="entity_A", relationship="owns"),
        NetworkEdge(source="entity_A", target="account_C", relationship="transacts"),
    ]

    return NetworkVisualization(
        case_id=case_id,
        nodes=nodes,
        edges=edges
    )

async def calculate_risk_exposure(entity_id: str) -> RiskExposure:
    """
    Calculates the risk exposure for a given entity.
    Mock implementation.
    """
    # Logic: fetch transaction history, sanctions list, etc.
    return RiskExposure(
        entity_id=entity_id,
        risk_score=85.5,
        risk_level="High",
        factors=["High-value transactions", "Transacts with high-risk jurisdiction"]
    )

async def auto_match_watchlist(transaction: Dict) -> List[WatchlistMatch]:
    """
    Checks if any entity involved in the transaction matches a watchlist.
    Mock implementation.
    """
    # Logic: Extract names from transaction, fuzzy match against WatchlistEntry
    matches = []

    # Mock check
    if "sender" in transaction and transaction["sender"] == "Bad Actor":
        matches.append(WatchlistMatch(
            match_id="m-001",
            watchlist_id=101,
            confidence_score=0.98,
            matched_name="Bad Actor",
            list_type="OFAC"
        ))

    return matches
