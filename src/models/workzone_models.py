from datetime import datetime
from typing import Any
from sqlalchemy import String, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from src.models.v2x_models import Base, utcnow

class WorkZone(Base):
    """
    Work Zone Management Model

    Attributes:
        id (int): Work Zone ID
        location (Geometry): Polygon geometry of the work zone (SRID 4326)
        contractor (str): Contractor name
        speed_limit (float): Speed limit in the work zone (km/h or m/s)
        closed_lanes (dict): JSON object describing closed lanes
        start_date (datetime): Start date/time of the work zone
        end_date (datetime): End date/time of the work zone
        status (str): Status of the work zone (e.g., 'active', 'completed')
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = "work_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326))
    contractor: Mapped[str] = mapped_column(String)
    speed_limit: Mapped[float] = mapped_column(Float)
    closed_lanes: Mapped[dict] = mapped_column(JSON)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
