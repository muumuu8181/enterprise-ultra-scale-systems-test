from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db
from src.models.chatbot_models import ChatSession, ChatMessage, SenderType, SessionStatus
from src.services.chatbot_engine import ChatbotEngine
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class SessionCreate(BaseModel):
    user_id: str

class SessionResponse(BaseModel):
    id: int
    user_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    session_id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    response: str
    message_id: int

class EscalateRequest(BaseModel):
    reason: str

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(user_id=request.user_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(session_id: int, request: MessageCreate, db: AsyncSession = Depends(get_db)):
    # Verify session exists
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
         raise HTTPException(status_code=400, detail="Session is not active")

    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        sender=SenderType.USER,
        content=request.content
    )
    db.add(user_message)
    await db.commit()

    # Process with Chatbot Engine
    engine = ChatbotEngine(db)
    response_text = await engine.process_message(session_id, request.content)

    # Save bot message
    bot_message = ChatMessage(
        session_id=session_id,
        sender=SenderType.BOT,
        content=response_text
    )
    db.add(bot_message)
    await db.commit()
    await db.refresh(bot_message)

    return {"response": response_text, "message_id": bot_message.id}

@router.get("/sessions/{session_id}/history", response_model=List[MessageResponse])
async def get_history(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp))
    messages = result.scalars().all()
    return messages

@router.post("/sessions/{session_id}/escalate")
async def escalate_session(session_id: int, request: EscalateRequest, db: AsyncSession = Depends(get_db)):
    engine = ChatbotEngine(db)
    try:
        ticket = await engine.handle_escalation(session_id, request.reason)
        return {"status": "escalated", "ticket_id": ticket.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
