from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SqEnum
import enum
from datetime import datetime, timezone
from src.database import Base

class CrewType(str, enum.Enum):
    baggage = "baggage"
    refuel = "refuel"
    catering = "catering"
    maintenance = "maintenance"

class CarouselStatus(str, enum.Enum):
    idle = "idle"
    running = "running"

class TurnaroundStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"

class GroundCrew(Base):
    __tablename__ = "ground_crews"

    id = Column(Integer, primary_key=True, index=True)
    crew_type = Column(SqEnum(CrewType), nullable=False)
    shift = Column(String, nullable=False)
    assigned_flight_id = Column(String, nullable=True)
    check_in_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Turnaround(Base):
    __tablename__ = "turnarounds"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(String, unique=True, index=True, nullable=False)
    target_minutes = Column(Integer, nullable=False)
    actual_minutes = Column(Integer, nullable=True)
    steps_completed = Column(JSON, default=list)
    status = Column(SqEnum(TurnaroundStatus), default=TurnaroundStatus.pending)

class BaggageCarousel(Base):
    __tablename__ = "baggage_carousels"

    id = Column(Integer, primary_key=True, index=True)
    terminal = Column(String, nullable=False)
    carousel_number = Column(Integer, nullable=False)
    status = Column(SqEnum(CarouselStatus), default=CarouselStatus.idle)
    assigned_flight_id = Column(String, nullable=True)
    bags_claimed = Column(Integer, default=0)
