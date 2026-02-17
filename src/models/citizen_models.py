from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, List, Any

class CitizenReport(Base):
    """
    市民からの通報モデル
    """
    __tablename__ = "citizen_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    photos: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="Pending") # Pending, In Progress, Resolved
    assigned_dept: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ServiceAppointment(Base):
    """
    行政サービス予約モデル
    """
    __tablename__ = "service_appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_id: Mapped[str] = mapped_column(String, index=True)
    citizen_id: Mapped[str] = mapped_column(String, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="Scheduled") # Scheduled, Completed, Cancelled
    queue_number: Mapped[int] = mapped_column(Integer)
