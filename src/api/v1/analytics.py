from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from src.core.database import get_db
from src.models.support_models import Ticket, CSATScore, Agent, TicketStatus
from src.services.sla_monitor import SLAMonitor
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/ticket-volume")
async def get_ticket_volume(period: str = "daily", db: AsyncSession = Depends(get_db)):
    """
    Get ticket volume for the specified period (daily/weekly).
    """
    now = datetime.utcnow()
    if period == "weekly":
        start_date = now - timedelta(weeks=1)
    else:
        start_date = now - timedelta(days=1)

    stmt = select(func.count(Ticket.id)).where(Ticket.created_at >= start_date)
    result = await db.execute(stmt)
    count = result.scalar() or 0

    return {"period": period, "count": count, "start_date": start_date}

@router.get("/resolution-time")
async def get_resolution_time(db: AsyncSession = Depends(get_db)):
    """
    Get average resolution time for resolved tickets.
    """
    # Calculate difference between resolved_at and created_at for resolved tickets
    # SQLite might not support complex date math easily in SQL, so we might fetch and calc in python for this mock
    # But let's try to be efficient.

    stmt = select(Ticket).where(Ticket.status == TicketStatus.RESOLVED)
    result = await db.execute(stmt)
    tickets = result.scalars().all()

    if not tickets:
        return {"average_resolution_hours": 0}

    total_time = 0
    count = 0
    for t in tickets:
        if t.resolved_at and t.created_at:
            delta = t.resolved_at - t.created_at
            total_time += delta.total_seconds()
            count += 1

    avg_seconds = total_time / count if count > 0 else 0
    avg_hours = avg_seconds / 3600

    return {"average_resolution_hours": round(avg_hours, 2)}

@router.get("/satisfaction-score")
async def get_satisfaction_score(db: AsyncSession = Depends(get_db)):
    """
    Get average CSAT score.
    """
    stmt = select(func.avg(CSATScore.score))
    result = await db.execute(stmt)
    avg_score = result.scalar() or 0

    return {"average_csat": round(avg_score, 2)}

@router.get("/agent-performance")
async def get_agent_performance(db: AsyncSession = Depends(get_db)):
    """
    Get performance metrics per agent.
    """
    # Number of resolved tickets per agent
    stmt = select(
        Agent.name,
        func.count(Ticket.id).label("resolved_count")
    ).outerjoin(Ticket, (Agent.id == Ticket.assigned_agent_id) & (Ticket.status == TicketStatus.RESOLVED))\
    .group_by(Agent.name)

    result = await db.execute(stmt)
    data = []
    for row in result:
        data.append({"agent": row.name, "resolved_tickets": row.resolved_count})

    return data

@router.get("/sla-metrics")
async def get_sla_metrics(db: AsyncSession = Depends(get_db)):
    monitor = SLAMonitor(db)
    return await monitor.calculate_sla_metrics()
