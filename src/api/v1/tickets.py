from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
from src.core.database import get_db
from src.models.support_models import Ticket, TicketMessage, TicketStatus, TicketPriority

router = APIRouter(prefix="/tickets", tags=["tickets"])

# Pydantic Models
class TicketCreate(BaseModel):
    subject: str
    description: str
    category: str
    priority: TicketPriority = TicketPriority.MEDIUM
    customer_id: int

class TicketMessageCreate(BaseModel):
    sender_id: int
    content: str
    attachments: Optional[dict] = None

class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    content: str
    attachments: Optional[dict] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketResponse(BaseModel):
    id: int
    customer_id: int
    subject: str
    description: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    assignee_id: Optional[int]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketUpdateStatus(BaseModel):
    status: TicketStatus

# Endpoints - Order matters!

@router.get("/queue", response_model=List[TicketResponse])
async def get_ticket_queue(
    assignee: Optional[str] = Query(None, description="Assignee ID or 'me'"),
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Ticket)

    if assignee:
        if assignee == "me":
            # Mocking "me" as user_id 1 for now since we don't have Auth context
            query = query.where(Ticket.assignee_id == 1)
        else:
            try:
                assignee_id = int(assignee)
                query = query.where(Ticket.assignee_id == assignee_id)
            except ValueError:
                pass # Ignore invalid integer conversion or handle error

    if status:
        query = query.where(Ticket.status == status)

    if priority:
        query = query.where(Ticket.priority == priority)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=TicketResponse)
async def create_ticket(ticket: TicketCreate, db: AsyncSession = Depends(get_db)):
    new_ticket = Ticket(
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=TicketStatus.OPEN,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    return new_ticket

@router.get("/{id}", response_model=TicketResponse)
async def get_ticket(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Ticket).where(Ticket.id == id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.post("/{id}/messages", response_model=TicketMessageResponse)
async def create_ticket_message(id: int, message: TicketMessageCreate, db: AsyncSession = Depends(get_db)):
    # Verify ticket exists
    stmt = select(Ticket).where(Ticket.id == id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    new_message = TicketMessage(
        ticket_id=id,
        sender_id=message.sender_id,
        content=message.content,
        attachments=message.attachments,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message

@router.put("/{id}/status", response_model=TicketResponse)
async def update_ticket_status(id: int, status_update: TicketUpdateStatus, db: AsyncSession = Depends(get_db)):
    stmt = select(Ticket).where(Ticket.id == id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status_update.status
    await db.commit()
    await db.refresh(ticket)
    return ticket
