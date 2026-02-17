from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ProposalStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"

class VoteType(str, Enum):
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"

class DAO(BaseModel):
    id: str
    name: str
    description: str
    treasury_address: str
    governance_token: str
    voting_quorum_pct: float
    execution_delay_hours: int
    member_count: int

class Proposal(BaseModel):
    id: str
    dao_id: str
    proposer_address: str
    title: str
    description: str
    actions: List[Dict[str, Any]]
    status: ProposalStatus
    votes_for: float
    votes_against: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Vote(BaseModel):
    id: str
    proposal_id: str
    voter_address: str
    vote: VoteType
    voting_power: float
    reason: Optional[str] = None
    voted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
