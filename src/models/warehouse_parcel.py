from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry
import enum
from datetime import datetime

Base = declarative_base()

class ScanMethod(enum.Enum):
    barcode = "barcode"
    rfid = "rfid"

class ReturnStatus(enum.Enum):
    initiated = "initiated"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"

class SortingFacility(Base):
    __tablename__ = 'sorting_facilities'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # location: GeoJSON. Using Geometry type which can be serialized to GeoJSON.
    # Assuming Point for location.
    location = Column(Geometry('POINT'), nullable=True)
    processing_capacity_per_day = Column(Integer, default=0)
    current_backlog = Column(Integer, default=0)

class SortingEvent(Base):
    __tablename__ = 'sorting_events'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey('sorting_facilities.id'), nullable=False)
    conveyor_line = Column(String, nullable=True)
    destination_bin = Column(String, nullable=True)
    sorted_at = Column(DateTime, default=datetime.utcnow)
    scan_method = Column(SAEnum(ScanMethod), nullable=False)

class ReturnRequest(Base):
    __tablename__ = 'return_requests'

    id = Column(Integer, primary_key=True)
    original_parcel_id = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=True)
    return_label = Column(String, nullable=True)
    refund_eligible = Column(Boolean, default=False)
    status = Column(SAEnum(ReturnStatus), default=ReturnStatus.initiated)
