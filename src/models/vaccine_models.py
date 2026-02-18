from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from datetime import datetime, timezone
from src.core.database import Base

class VaccineBatch(Base):
    __tablename__ = "vaccine_batches"

    id = Column(Integer, primary_key=True, index=True)
    vaccine_type = Column(String, index=True)
    manufacturer = Column(String)
    lot_number = Column(String, unique=True, index=True)
    quantity = Column(Integer)
    expiry_date = Column(DateTime)
    cold_chain_required = Column(Boolean, default=True)
    current_location_id = Column(Integer, ForeignKey("distribution_centers.id"), nullable=True)

class DistributionCenter(Base):
    __tablename__ = "distribution_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    # Using JSON for spatial storage since SpatiaLite is not guaranteed.
    location = Column(JSON)
    storage_capacity = Column(Integer)
    cold_chain_certified = Column(Boolean, default=False)
    current_inventory = Column(JSON)

class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    vaccine_type = Column(String)
    dose_number = Column(Integer)
    administered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    site_id = Column(Integer, ForeignKey("distribution_centers.id"))
    lot_number = Column(String)
    next_dose_date = Column(DateTime, nullable=True)
