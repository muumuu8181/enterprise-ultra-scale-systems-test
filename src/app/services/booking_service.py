from sqlalchemy.orm import Session
from src.app.models.booking import Booking, BookingStatus
from src.app.models.flight import Seat
from src.app.schemas.booking import BookingCreate
import uuid

def generate_pnr():
    return str(uuid.uuid4()).split('-')[0].upper()

def create_booking(db: Session, booking: BookingCreate):
    # Check seat availability if seat is selected
    if booking.seat_id:
        # Use with_for_update to lock the row for update
        seat = db.query(Seat).filter(Seat.id == booking.seat_id).with_for_update().first()

        if not seat:
            raise ValueError("Seat not found")
        if seat.is_booked:
            raise ValueError("Seat already booked")

        seat.is_booked = True
        db.add(seat)

    db_booking = Booking(
        pnr=generate_pnr(),
        flight_id=booking.flight_id,
        seat_id=booking.seat_id,
        passenger_name=booking.passenger_name,
        passenger_email=booking.passenger_email,
        status=BookingStatus.CONFIRMED if booking.seat_id else BookingStatus.PENDING
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_booking(db: Session, pnr: str):
    return db.query(Booking).filter(Booking.pnr == pnr).first()
