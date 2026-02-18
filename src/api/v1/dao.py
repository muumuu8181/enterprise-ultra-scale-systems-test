from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from src.models.dao_models import DAO, Proposal, Vote, ProposalStatus, VoteType
from src.services.governance_service import calculate_voting_power, check_quorum, execute_proposal, ExecutionResult

router = APIRouter()

# In-memory storage
daos = {}
proposals = {}
votes = {}

@router.post("/daos/create", response_model=DAO)
async def create_dao(dao: DAO):
    if dao.id in daos:
        raise HTTPException(status_code=400, detail="DAO already exists")
    daos[dao.id] = dao
    return dao

@router.get("/daos/{id}/dashboard", response_model=DAO)
async def get_dao_dashboard(id: str):
    if id not in daos:
        raise HTTPException(status_code=404, detail="DAO not found")
    return daos[id]

@router.get("/daos/{id}/proposals", response_model=List[Proposal])
async def list_proposals(id: str, status: Optional[ProposalStatus] = Query(None)):
    if id not in daos:
        raise HTTPException(status_code=404, detail="DAO not found")

    dao_proposals = [p for p in proposals.values() if p.dao_id == id]

    if status:
        dao_proposals = [p for p in dao_proposals if p.status == status]

    return dao_proposals

@router.post("/proposals/create", response_model=Proposal)
async def create_proposal(proposal: Proposal):
    if proposal.dao_id not in daos:
        raise HTTPException(status_code=404, detail="DAO not found")
    if proposal.id in proposals:
        raise HTTPException(status_code=400, detail="Proposal already exists")

    proposals[proposal.id] = proposal
    return proposal

@router.post("/proposals/{id}/vote", response_model=Vote)
async def vote_on_proposal(id: str, vote: Vote):
    if id not in proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if vote.proposal_id != id:
         raise HTTPException(status_code=400, detail="Proposal ID mismatch")

    # Mock logic: Calculate voting power and update proposal
    power = await calculate_voting_power(vote.voter_address, proposals[id].dao_id)
    vote.voting_power = power

    votes[vote.id] = vote

    proposal = proposals[id]
    if vote.vote == VoteType.FOR:
        proposal.votes_for += power
    elif vote.vote == VoteType.AGAINST:
        proposal.votes_against += power

    return vote

@router.post("/proposals/{id}/execute", response_model=ExecutionResult)
async def execute_proposal_endpoint(id: str):
    if id not in proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal = proposals[id]

    quorum_reached = await check_quorum(id)
    if not quorum_reached:
         raise HTTPException(status_code=400, detail="Quorum not reached")

    result = await execute_proposal(id)

    if result.success:
        proposal.status = ProposalStatus.EXECUTED

    return result
