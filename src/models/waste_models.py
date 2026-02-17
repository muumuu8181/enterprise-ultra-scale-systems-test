from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import Optional, List, Dict, Any

class WasteBin(Base):
    """
    ゴミ箱モデル
    """
    __tablename__ = "waste_bins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # PostGISのPOINT型 (SRID 4326: WGS84)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    district: Mapped[str] = mapped_column(String, index=True)
    bin_type: Mapped[str] = mapped_column(String) # recyclable, burnable, etc.
    capacity_liters: Mapped[int] = mapped_column(Integer)
    fill_level: Mapped[float] = mapped_column(Float, default=0.0) # 0.0 to 100.0 or actual volume? Assume percentage 0-100 based on fill-level endpoint logic
    last_collected: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CollectionRoute(Base):
    """
    収集ルートモデル
    """
    __tablename__ = "collection_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    driver_id: Mapped[str] = mapped_column(String)
    waypoints: Mapped[List[Dict[str, Any]]] = mapped_column(JSON) # List of point coordinates or bin IDs
    total_distance_km: Mapped[float] = mapped_column(Float)
    estimated_duration_min: Mapped[float] = mapped_column(Float)
