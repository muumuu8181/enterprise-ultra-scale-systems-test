from sqlalchemy.orm import Session
from src.app.models.flight import Flight, Seat
from src.app.schemas.flight import FlightCreate

def create_flight(db: Session, flight: FlightCreate):
    db_flight = Flight(
        flight_number=flight.flight_number,
        origin=flight.origin,
        destination=flight.destination,
        departure_time=flight.departure_time,
        capacity=flight.capacity
    )
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)

    for seat in flight.seats:
        db_seat = Seat(
            flight_id=db_flight.id,
            seat_number=seat.seat_number,
            class_type=seat.class_type,
            is_booked=seat.is_booked
        )
        db.add(db_seat)

    db.commit()
    db.refresh(db_flight)
    return db_flight

def search_flights(db: Session, origin: str, destination: str):
    return db.query(Flight).filter(Flight.origin == origin, Flight.destination == destination).all()

def get_flight(db: Session, flight_id: int):
    return db.query(Flight).filter(Flight.id == flight_id).first()
