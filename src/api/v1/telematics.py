from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.rental_models import Vehicle, TelematicsData, Booking, VehicleAlert
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    speed: float
    fuel_level: float

class AlertCreate(BaseModel):
    type: str # breakdown, accident, geofence_violation
    details: Optional[str] = None

class TripSummary(BaseModel):
    booking_id: int
    total_distance: float
    average_speed: float
    start_time: datetime
    end_time: Optional[datetime]

@router.post("/{vehicle_id}/location")
def update_location(vehicle_id: int, update: LocationUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Update current vehicle status
    vehicle.latitude = update.latitude
    vehicle.longitude = update.longitude
    vehicle.current_speed = update.speed
    vehicle.fuel_level = update.fuel_level

    # Log telematics data
    log = TelematicsData(
        vehicle_id=vehicle_id,
        latitude=update.latitude,
        longitude=update.longitude,
        speed=update.speed,
        fuel_level=update.fuel_level
    )
    db.add(log)
    db.commit()
    return {"status": "updated"}

@router.get("/{booking_id}/trip-summary", response_model=TripSummary)
def get_trip_summary(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    logs = db.query(TelematicsData).filter(
        TelematicsData.vehicle_id == booking.vehicle_id,
        TelematicsData.timestamp >= booking.start_time
    ).all()

    if booking.end_time:
        logs = [l for l in logs if l.timestamp <= booking.end_time]

    if not logs:
        return TripSummary(
            booking_id=booking_id,
            total_distance=0.0,
            average_speed=0.0,
            start_time=booking.start_time,
            end_time=booking.end_time
        )

    # Simple logic
    avg_speed = sum(l.speed for l in logs) / len(logs)

    return TripSummary(
        booking_id=booking_id,
        total_distance=len(logs) * 1.0, # Placeholder: 1 unit per log
        average_speed=avg_speed,
        start_time=booking.start_time,
        end_time=booking.end_time
    )

@router.post("/{vehicle_id}/alert")
def create_alert(vehicle_id: int, alert: AlertCreate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    new_alert = VehicleAlert(
        vehicle_id=vehicle_id,
        alert_type=alert.type,
        resolved=False
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return {"status": "alert_received", "alert_id": new_alert.id}
