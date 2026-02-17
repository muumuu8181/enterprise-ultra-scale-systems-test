from celery import Celery
import os
from src.models.secondary_market import SecondaryListing, TransferRecord, Waitlist, ListingStatus, TransferType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional

# Configure Celery
celery_app = Celery("secondary_market", broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

class ResaleResult(BaseModel):
    success: bool
    message: str
    transfer_id: Optional[int] = None

async def validate_ticket_authenticity(ticket_id: str) -> bool:
    """
    Mock implementation to validate ticket authenticity.
    In a real system, this would check against a primary ticketing service or blockchain.
    """
    # Simulate a check. For now, assume all tickets starting with "VALID" are valid, or just return True.
    return True

async def process_resale(db: AsyncSession, listing_id: int, buyer_id: str) -> ResaleResult:
    """
    Process a ticket resale:
    1. Verify listing exists and is active.
    2. Verify ticket authenticity.
    3. Update listing status to SOLD.
    4. Create TransferRecord.
    5. Return result.
    """
    # Use with_for_update to lock the row and prevent race conditions
    result = await db.execute(select(SecondaryListing).where(SecondaryListing.id == listing_id).with_for_update())
    listing = result.scalar_one_or_none()

    if not listing:
        return ResaleResult(success=False, message="Listing not found")

    if listing.status != ListingStatus.LISTED:
        return ResaleResult(success=False, message="Listing is not available")

    is_valid = await validate_ticket_authenticity(listing.ticket_id)
    if not is_valid:
        return ResaleResult(success=False, message="Ticket is invalid")

    # Update listing
    listing.status = ListingStatus.SOLD

    # Create transfer record
    transfer = TransferRecord(
        ticket_id=listing.ticket_id,
        from_user=listing.seller_id,
        to_user=buyer_id,
        transfer_type=TransferType.RESALE,
        transfer_price=listing.asking_price
    )
    db.add(transfer)

    try:
        await db.commit()
        await db.refresh(transfer)
        return ResaleResult(success=True, message="Resale processed successfully", transfer_id=transfer.id)
    except Exception as e:
        await db.rollback()
        return ResaleResult(success=False, message=str(e))

@celery_app.task
def send_waitlist_notification(event_id: str, available_quantity: int):
    """
    Celery task to actually send notifications.
    """
    # This would typically fetch users from DB and send emails/push notifs.
    # For now, we just print/log.
    print(f"Notification sent to waitlist for event {event_id}. Quantity available: {available_quantity}")
    return f"Notified waitlist for {event_id}"

async def notify_waitlist(event_id: str, available_quantity: int):
    """
    Service function to trigger waitlist notification.
    """
    send_waitlist_notification.delay(event_id, available_quantity)
