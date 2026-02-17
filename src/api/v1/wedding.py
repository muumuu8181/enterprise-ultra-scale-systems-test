from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, EmailStr
from src.database import get_db
from src.models.wedding_models import Wedding, Vendor, GuestList, WeddingStatus, VendorType, RSVPStatus

router = APIRouter()

# --- Pydantic Schemas ---

class WeddingCreate(BaseModel):
    couple_names: str
    wedding_date: date
    guest_count: int
    budget: float
    theme: str
    coordinator_id: Optional[int] = None

class WeddingResponse(BaseModel):
    id: int
    couple_names: str
    wedding_date: date
    status: WeddingStatus
    guest_count: int
    budget: float
    confirmed_vendors: List[str] = []

    class Config:
        from_attributes = True

class VendorResponse(BaseModel):
    id: int
    name: str
    vendor_type: VendorType
    price_range: str
    rating: float
    location: str

    class Config:
        from_attributes = True

class GuestCreate(BaseModel):
    guest_name: str
    email: Optional[EmailStr] = None
    party_size: int = 1
    meal_preference: Optional[str] = None
    dietary_restrictions: Optional[str] = None

class GuestImport(BaseModel):
    wedding_id: int
    guests: List[GuestCreate]

class GuestRSVP(BaseModel):
    rsvp_status: RSVPStatus
    meal_preference: Optional[str] = None

class BudgetBreakdown(BaseModel):
    total_budget: float
    spent: float
    remaining: float
    breakdown: Dict[str, float]

class ChecklistItem(BaseModel):
    task: str
    due_date: date
    completed: bool

class SeatingChart(BaseModel):
    tables: Dict[int, List[str]]

# --- API Endpoints ---

@router.get("/weddings/{id}/dashboard", response_model=WeddingResponse)
def get_wedding_dashboard(id: int, db: Session = Depends(get_db)):
    wedding = db.query(Wedding).filter(Wedding.id == id).first()
    if not wedding:
        raise HTTPException(status_code=404, detail="Wedding not found")

    response = WeddingResponse.model_validate(wedding)
    response.confirmed_vendors = [v.name for v in wedding.vendors]
    return response

@router.post("/weddings/create", response_model=WeddingResponse)
def create_wedding(wedding: WeddingCreate, db: Session = Depends(get_db)):
    db_wedding = Wedding(**wedding.model_dump())
    db.add(db_wedding)
    db.commit()
    db.refresh(db_wedding)
    return db_wedding

@router.get("/vendors/search", response_model=List[VendorResponse])
def search_vendors(
    type: Optional[VendorType] = None,
    date: Optional[date] = None,
    budget: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Vendor)
    if type:
        query = query.filter(Vendor.vendor_type == type)
    # Note: 'date' availability check and 'budget' filtering logic would be more complex in real implementation
    # For now, we return all matching types
    vendors = query.all()
    return vendors

@router.post("/vendors/{id}/book")
def book_vendor(id: int, wedding_id: int = Query(...), db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == id).first()
    wedding = db.query(Wedding).filter(Wedding.id == wedding_id).first()

    if not vendor or not wedding:
        raise HTTPException(status_code=404, detail="Vendor or Wedding not found")

    wedding.vendors.append(vendor)
    db.commit()
    return {"message": "Vendor booked successfully"}

@router.post("/guests/import")
def import_guests(data: GuestImport, db: Session = Depends(get_db)):
    count = 0
    for g in data.guests:
        db_guest = GuestList(
            wedding_id=data.wedding_id,
            guest_name=g.guest_name,
            email=g.email,
            party_size=g.party_size,
            meal_preference=g.meal_preference,
            dietary_restrictions=g.dietary_restrictions
        )
        db.add(db_guest)
        count += 1
    db.commit()
    return {"message": f"Imported {count} guests"}

@router.put("/guests/{id}/rsvp")
def update_rsvp(id: int, rsvp: GuestRSVP, db: Session = Depends(get_db)):
    guest = db.query(GuestList).filter(GuestList.id == id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    guest.rsvp_status = rsvp.rsvp_status
    if rsvp.meal_preference:
        guest.meal_preference = rsvp.meal_preference

    db.commit()
    return {"message": "RSVP updated"}

@router.get("/budget/{wedding_id}/breakdown", response_model=BudgetBreakdown)
def get_budget_breakdown(wedding_id: int, db: Session = Depends(get_db)):
    wedding = db.query(Wedding).filter(Wedding.id == wedding_id).first()
    if not wedding:
        raise HTTPException(status_code=404, detail="Wedding not found")

    # Mock calculation
    spent = 0.0 # calculate from vendors/invoices
    return BudgetBreakdown(
        total_budget=wedding.budget,
        spent=spent,
        remaining=wedding.budget - spent,
        breakdown={"venue": 0.0, "catering": 0.0}
    )

@router.get("/timeline/{wedding_id}/checklist", response_model=List[ChecklistItem])
def get_timeline_checklist(wedding_id: int, db: Session = Depends(get_db)):
    # Mock checklist
    return [
        ChecklistItem(task="Book Venue", due_date=date.today(), completed=False),
        ChecklistItem(task="Send Invitations", due_date=date.today(), completed=False)
    ]

@router.get("/seating/{wedding_id}/chart", response_model=SeatingChart)
def get_seating_chart(wedding_id: int, db: Session = Depends(get_db)):
    guests = db.query(GuestList).filter(GuestList.wedding_id == wedding_id).all()
    tables = {}
    for guest in guests:
        if guest.table_number:
            if guest.table_number not in tables:
                tables[guest.table_number] = []
            tables[guest.table_number].append(guest.guest_name)

    return SeatingChart(tables=tables)
