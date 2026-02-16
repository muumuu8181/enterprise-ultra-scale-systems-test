from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.app.schemas.flight import Flight, FlightCreate
from src.app.schemas.booking import Booking, BookingCreate
from src.app.services.inventory_service import create_flight, search_flights
from src.app.services.booking_service import create_booking, get_booking as get_booking_service
from src.app.database import get_db

router = APIRouter()

@router.post("/flights/", response_model=Flight)
def create_new_flight(flight: FlightCreate, db: Session = Depends(get_db)):
    return create_flight(db, flight)

@router.get("/flights/", response_model=List[Flight])
def search_flights_route(origin: str, destination: str, db: Session = Depends(get_db)):
    return search_flights(db, origin, destination)

@router.post("/bookings/", response_model=Booking)
def create_new_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    try:
        return create_booking(db, booking)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bookings/{pnr}", response_model=Booking)
def get_booking_route(pnr: str, db: Session = Depends(get_db)):
    booking = get_booking_service(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
