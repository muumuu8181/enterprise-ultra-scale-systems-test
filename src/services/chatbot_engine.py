from sqlalchemy.ext.asyncio import AsyncSession
from src.models.support_models import Ticket, TicketPriority, TicketStatus
from src.models.chatbot_models import ChatSession, SessionStatus
from datetime import datetime, timedelta

class ChatbotEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def classify_intent(self, text: str) -> str:
        """
        Classify the intent of the user's message using an LLM (mocked).
        """
        text_lower = text.lower()
        if "escalate" in text_lower or "human" in text_lower or "agent" in text_lower:
            return "escalate"
        elif "help" in text_lower:
            return "help"
        elif "refund" in text_lower:
            return "refund_request"
        else:
            return "general_inquiry"

    async def retrieve_answer(self, query: str) -> str:
        """
        Retrieve relevant information from the Knowledge Base using RAG (mocked).
        """
        # In a real system, this would query a vector database.
        return f"Relevant policy for '{query}' found in KB."

    async def generate_response(self, intent: str, context: str) -> str:
        """
        Generate a response using GPT-4 (mocked).
        """
        if intent == "escalate":
            return "I understand you want to speak with a human agent. I am escalating your request now."
        elif intent == "refund_request":
            return f"I can help with refunds. Based on our policy: {context}. Please provide your order ID."
        else:
            return f"Here is some information regarding your query: {context}"

    async def handle_escalation(self, session_id: int, reason: str) -> Ticket:
        """
        Escalate the session to a human agent by creating a support ticket.
        """
        # Find the session
        session = await self.db.get(ChatSession, session_id)
        if not session:
            raise ValueError("Session not found")

        # Update session status
        session.status = SessionStatus.ESCALATED

        # Create a ticket
        # In a real app, we might look up the user from the session
        new_ticket = Ticket(
            user_id=session.user_id,
            subject=f"Escalation from Chat Session {session_id}",
            description=f"Reason: {reason}",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH, # Escalations are usually high priority
            sla_due_at=datetime.utcnow() + timedelta(hours=4) # 4 hour SLA for example
        )
        self.db.add(new_ticket)
        await self.db.commit()
        await self.db.refresh(new_ticket)

        return new_ticket

    async def process_message(self, session_id: int, message_content: str) -> str:
        """
        Orchestrator method to process a message and return a response.
        """
        intent = await self.classify_intent(message_content)

        if intent == "escalate":
            await self.handle_escalation(session_id, reason="User requested escalation")
            return await self.generate_response(intent, "")

        context = await self.retrieve_answer(message_content)
        response = await self.generate_response(intent, context)
        return response
