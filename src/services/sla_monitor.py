from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from src.models.support_models import Ticket, TicketStatus
from datetime import datetime

class SLAMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_sla_breach(self, ticket_id: int) -> bool:
        """
        Check if a specific ticket has breached its SLA.
        """
        result = await self.db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalars().first()
        if not ticket:
            return False

        if ticket.resolved_at:
            return ticket.resolved_at > ticket.sla_due_at

        # If not resolved, check current time
        return datetime.utcnow() > ticket.sla_due_at

    async def send_escalation_alert(self, ticket_id: int):
        """
        Send an alert if a ticket is approaching or has breached SLA (Mocked).
        """
        # In a real system, this would integrate with email or Slack API
        print(f"ALERT: Ticket {ticket_id} has breached SLA!")

    async def calculate_sla_metrics(self) -> dict:
        """
        Calculate overall SLA compliance metrics.
        Returns:
            dict: {
                "total_tickets": int,
                "sla_breached": int,
                "sla_met": int,
                "compliance_rate": float
            }
        """
        # Count total tickets
        total_stmt = select(func.count(Ticket.id))
        total_result = await self.db.execute(total_stmt)
        total_tickets = total_result.scalar() or 0

        if total_tickets == 0:
             return {
                "total_tickets": 0,
                "sla_breached": 0,
                "sla_met": 0,
                "compliance_rate": 100.0
            }

        # Count breaches (resolved late or currently open and late)
        breach_stmt = select(func.count(Ticket.id)).where(
            ((Ticket.resolved_at != None) & (Ticket.resolved_at > Ticket.sla_due_at)) |
            ((Ticket.resolved_at == None) & (datetime.utcnow() > Ticket.sla_due_at))
        )
        breach_result = await self.db.execute(breach_stmt)
        sla_breached = breach_result.scalar() or 0

        sla_met = total_tickets - sla_breached
        compliance_rate = (sla_met / total_tickets) * 100

        return {
            "total_tickets": total_tickets,
            "sla_breached": sla_breached,
            "sla_met": sla_met,
            "compliance_rate": round(compliance_rate, 2)
        }
