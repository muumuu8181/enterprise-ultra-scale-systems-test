from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...database import get_db
from ...models.zoo_models import Animal, Enclosure, VeterinaryRecord, Biome, ConservationStatus, RecordType

router = APIRouter(prefix="/zoo", tags=["zoo"])

@router.get("/animals")
def get_animals(
    species: Optional[str] = Query(None),
    status: Optional[ConservationStatus] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Animal)
    if species:
        query = query.filter(Animal.species == species)
    if status:
        query = query.filter(Animal.conservation_status == status)
    return query.all()

@router.get("/animals/{id}/medical-history")
def get_medical_history(id: int, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.id == id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal.medical_records

@router.get("/enclosures")
def get_enclosures(biome: Optional[Biome] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Enclosure)
    if biome:
        query = query.filter(Enclosure.biome == biome)
    return query.all()

@router.post("/enclosures/{id}/maintenance-log")
def log_maintenance(id: int, log_data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    enclosure = db.query(Enclosure).filter(Enclosure.id == id).first()
    if not enclosure:
        raise HTTPException(status_code=404, detail="Enclosure not found")

    # Simple logic to append log to maintenance_schedule
    # Assuming maintenance_schedule is a dictionary with a 'logs' list
    current_schedule = enclosure.maintenance_schedule
    if not current_schedule:
        current_schedule = {"logs": []}
    elif isinstance(current_schedule, list):
         # If it was initialized as list somehow, wrap it
         current_schedule = {"logs": current_schedule}
    elif "logs" not in current_schedule:
         current_schedule["logs"] = []

    current_schedule["logs"].append(log_data)

    enclosure.maintenance_schedule = current_schedule
    flag_modified(enclosure, "maintenance_schedule")

    db.commit()
    db.refresh(enclosure)
    return {"message": "Maintenance log updated", "schedule": enclosure.maintenance_schedule}

@router.post("/vet-records/create")
def create_vet_record(record_data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    # Note: record_data should contain keys matching VeterinaryRecord fields
    # In production, use Pydantic model
    try:
        # manual handling for date parsing if string is passed
        if "date" in record_data and isinstance(record_data["date"], str):
             record_data["date"] = datetime.fromisoformat(record_data["date"].replace("Z", "+00:00"))

        new_record = VeterinaryRecord(**record_data)
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vet-records/upcoming-checkups")
def get_upcoming_checkups(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    records = db.query(VeterinaryRecord).filter(VeterinaryRecord.next_followup > now).all()
    return records

@router.get("/conservation/breeding-program")
def get_breeding_program():
    return {"status": "active", "programs": ["Panda", "Tiger", "Eagle"]}

@router.get("/analytics/visitor-flow")
def get_visitor_flow():
    return {"daily_average": 1500, "hotspots": ["Lion Den", "Penguin Cove"]}

@router.post("/enrichment/schedule")
def schedule_enrichment(schedule_data: Dict[str, Any] = Body(...)):
    return {"message": "Enrichment scheduled", "data": schedule_data}
