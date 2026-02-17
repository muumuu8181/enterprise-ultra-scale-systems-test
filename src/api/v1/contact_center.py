from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.core.database import get_db
from src.models.contact_center import ContactCenterQueue, AgentStatus, QualityScore, AgentStatusEnum, OverflowAction
from src.services import queue_service

router = APIRouter(prefix="/contact-center", tags=["contact-center"])

# Pydantic models
class QueueStatusResponse(BaseModel):
    queue_id: int
    name: str
    current_length: int
    estimated_wait_sec: int
    model_config = ConfigDict(from_attributes=True)

class JoinAgentRequest(BaseModel):
    agent_id: int

class AgentDashboardResponse(BaseModel):
    agent_id: int
    status: AgentStatusEnum
    current_call_id: Optional[int]
    handled_today: int
    avg_handle_time_sec: float
    model_config = ConfigDict(from_attributes=True)

class TransferCallRequest(BaseModel):
    target_queue_id: Optional[int] = None
    target_agent_id: Optional[int] = None

class QualityScoreCreate(BaseModel):
    empathy_score: float
    resolution_score: float
    compliance_score: float
    supervisor_id: Optional[int] = None

class QualityScoreResponse(BaseModel):
    id: int
    call_id: int
    overall: float
    empathy_score: float
    resolution_score: float
    compliance_score: float
    model_config = ConfigDict(from_attributes=True)

class CSATReport(BaseModel):
    average_overall_score: float
    total_calls_monitored: int

# Endpoints

@router.get("/queues/{id}/status", response_model=QueueStatusResponse)
async def get_queue_status(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(ContactCenterQueue).where(ContactCenterQueue.id == id)
    result = await db.execute(stmt)
    queue = result.scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    wait_time = await queue_service.calculate_estimated_wait(id, db)

    return QueueStatusResponse(
        queue_id=queue.id,
        name=queue.name,
        current_length=queue.current_length,
        estimated_wait_sec=wait_time
    )

@router.post("/queues/{id}/join-agent")
async def join_agent(id: int, request: JoinAgentRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(ContactCenterQueue).where(ContactCenterQueue.id == id)
    result = await db.execute(stmt)
    queue = result.scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # Add agent to queue.agent_ids
    # Note: queue.agent_ids is a JSON list.
    current_agents = list(queue.agent_ids) if queue.agent_ids else []
    if request.agent_id not in current_agents:
        current_agents.append(request.agent_id)
        queue.agent_ids = current_agents
        await db.commit()

    return {"message": "Agent joined queue"}

@router.get("/agents/{id}/dashboard", response_model=AgentDashboardResponse)
async def get_agent_dashboard(id: int, db: AsyncSession = Depends(get_db)):
    # Try to find by agent_id first, then by PK
    stmt = select(AgentStatus).where(AgentStatus.agent_id == id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        # Check if it exists by PK
        stmt2 = select(AgentStatus).where(AgentStatus.id == id)
        result2 = await db.execute(stmt2)
        agent = result2.scalar_one_or_none()

        if not agent:
             raise HTTPException(status_code=404, detail="Agent status not found")

    return agent

@router.post("/calls/{id}/transfer")
async def transfer_call(id: int, request: TransferCallRequest, db: AsyncSession = Depends(get_db)):
    # Logic to transfer call.
    # Find agent handling this call
    stmt = select(AgentStatus).where(AgentStatus.current_call_id == id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if agent:
        # Free the agent
        agent.status = AgentStatusEnum.AVAILABLE
        agent.current_call_id = None
        await db.commit()

    return {"message": "Call transferred"}

@router.post("/calls/{id}/quality-score", response_model=QualityScoreResponse)
async def create_quality_score(id: int, score: QualityScoreCreate, db: AsyncSession = Depends(get_db)):
    new_score = QualityScore(
        call_id=id,
        supervisor_id=score.supervisor_id,
        empathy_score=score.empathy_score,
        resolution_score=score.resolution_score,
        compliance_score=score.compliance_score,
        overall=(score.empathy_score + score.resolution_score + score.compliance_score) / 3
    )
    db.add(new_score)
    await db.commit()
    await db.refresh(new_score)
    return new_score

@router.get("/analytics/csat-report", response_model=CSATReport)
async def get_csat_report(db: AsyncSession = Depends(get_db)):
    stmt = select(func.avg(QualityScore.overall), func.count(QualityScore.id))
    result = await db.execute(stmt)
    row = result.one()
    avg_score = row[0]
    count = row[1]

    return CSATReport(
        average_overall_score=avg_score if avg_score else 0.0,
        total_calls_monitored=count if count else 0
    )
