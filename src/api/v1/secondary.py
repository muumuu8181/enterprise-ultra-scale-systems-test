from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from src.core.database import get_db
from src.models.secondary_market import SecondaryListing, TransferRecord, Waitlist, ListingStatus, TransferType
from src.services.secondary_service import process_resale, validate_ticket_authenticity
from pydantic import BaseModel

router = APIRouter()

class ListingCreate(BaseModel):
    ticket_id: str
    seller_id: str
    asking_price: float
    platform_fee_pct: float

class PurchaseRequest(BaseModel):
    buyer_id: str

class TransferRequest(BaseModel):
    from_user: str
    to_user: str
    transfer_type: TransferType
    transfer_price: Optional[float] = None

@router.post("/listings/create", status_code=status.HTTP_201_CREATED)
async def create_listing(listing: ListingCreate, db: AsyncSession = Depends(get_db)):
    # Validate ticket authenticity
    if not await validate_ticket_authenticity(listing.ticket_id):
        raise HTTPException(status_code=400, detail="Invalid ticket")

    new_listing = SecondaryListing(
        ticket_id=listing.ticket_id,
        seller_id=listing.seller_id,
        asking_price=listing.asking_price,
        platform_fee_pct=listing.platform_fee_pct,
        status=ListingStatus.LISTED
    )
    db.add(new_listing)
    await db.commit()
    await db.refresh(new_listing)
    return new_listing

@router.get("/listings")
async def get_listings(event_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    # Note: filtering by event_id is limited as SecondaryListing does not store event_id directly.
    # In a real system, we would join with a Ticket table or Parse ticket_id.
    query = select(SecondaryListing).where(SecondaryListing.status == ListingStatus.LISTED)
    result = await db.execute(query)
    listings = result.scalars().all()
    # If we could filter by event_id, we would do it here.
    return listings

@router.post("/listings/{id}/purchase")
async def purchase_listing(id: int, purchase: PurchaseRequest, db: AsyncSession = Depends(get_db)):
    result = await process_resale(db, id, purchase.buyer_id)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result

@router.post("/tickets/{id}/transfer")
async def transfer_ticket(id: str, transfer: TransferRequest, db: AsyncSession = Depends(get_db)):
    record = TransferRecord(
        ticket_id=id,
        from_user=transfer.from_user,
        to_user=transfer.to_user,
        transfer_type=transfer.transfer_type,
        transfer_price=transfer.transfer_price
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

@router.get("/waitlist/{event_id}/join")
async def join_waitlist(
    event_id: str,
    user_id: str,
    tier_preference: str,
    max_price: float,
    db: AsyncSession = Depends(get_db)
):
    entry = Waitlist(
        event_id=event_id,
        user_id=user_id,
        tier_preference=tier_preference,
        max_price=max_price
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"message": "Joined waitlist", "id": entry.id}

@router.get("/waitlist/{event_id}/position")
async def get_waitlist_position(event_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    query_user = select(Waitlist).where(Waitlist.event_id == event_id, Waitlist.user_id == user_id)
    result_user = await db.execute(query_user)
    user_entry = result_user.scalar_one_or_none()

    if not user_entry:
        raise HTTPException(status_code=404, detail="User not in waitlist")

    query_position = select(func.count()).where(
        Waitlist.event_id == event_id,
        Waitlist.joined_at < user_entry.joined_at
    )
    result_pos = await db.execute(query_position)
    position = result_pos.scalar_one() + 1

    return {"position": position, "status": "waiting"}
