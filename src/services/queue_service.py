from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.contact_center import AgentStatus, ContactCenterQueue, QualityScore, AgentStatusEnum
import random

async def route_call(call_id: int, db: AsyncSession) -> AgentStatus:
    """
    Routes a call to an available agent.
    For simplicity, finds the first available agent.
    In a real scenario, this would consider queue assignment, skills, etc.
    """
    stmt = select(AgentStatus).where(AgentStatus.status == AgentStatusEnum.AVAILABLE)
    result = await db.execute(stmt)
    agent = result.scalars().first()

    if agent:
        agent.status = AgentStatusEnum.BUSY
        agent.current_call_id = call_id
        await db.commit()
        await db.refresh(agent)
        return agent

    return None

async def calculate_estimated_wait(queue_id: int, db: AsyncSession) -> int:
    stmt = select(ContactCenterQueue).where(ContactCenterQueue.id == queue_id)
    result = await db.execute(stmt)
    queue = result.scalar_one_or_none()

    if not queue:
        return 0

    if queue.current_length == 0:
        return 0

    # Get agents for this queue
    # queue.agent_ids is a JSON list of ints. If None or empty, default wait.
    if not queue.agent_ids:
        return queue.current_length * 300 # Default 5 min per call if no agents

    # Calculate average handle time of agents in this queue
    agent_stmt = select(AgentStatus).where(AgentStatus.agent_id.in_(queue.agent_ids))
    agent_result = await db.execute(agent_stmt)
    agents = agent_result.scalars().all()

    if not agents:
         return queue.current_length * 300

    total_avg_time = sum([a.avg_handle_time_sec for a in agents])
    avg_time = total_avg_time / len(agents) if len(agents) > 0 else 300

    if avg_time == 0:
        avg_time = 300

    # Estimated wait = (queue_length * avg_time) / num_agents
    estimated_wait = (queue.current_length * avg_time) / len(agents)
    return int(estimated_wait)

async def auto_quality_monitor(call_id: int, db: AsyncSession) -> QualityScore:
    # Mock implementation
    score = QualityScore(
        call_id=call_id,
        empathy_score=round(random.uniform(1, 5), 1),
        resolution_score=round(random.uniform(1, 5), 1),
        compliance_score=round(random.uniform(1, 5), 1),
        overall=0.0
    )
    score.overall = round((score.empathy_score + score.resolution_score + score.compliance_score) / 3, 1)

    db.add(score)
    await db.commit()
    await db.refresh(score)
    return score
