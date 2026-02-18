from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import JSON
from geoalchemy2 import Geometry
from src.database import Base
from datetime import datetime
from typing import List, Any

class TransitVehicle(Base):
    """
    公共交通車両モデル
    """
    __tablename__ = "transit_vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    route_id: Mapped[str] = mapped_column(String, index=True)
    operator: Mapped[str] = mapped_column(String)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    speed: Mapped[float] = mapped_column(Float)
    heading: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    predictions: Mapped[List["ArrivalPrediction"]] = relationship("ArrivalPrediction", back_populates="vehicle")

class TransitStop(Base):
    """
    バス停・駅モデル
    """
    __tablename__ = "transit_stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stop_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    routes: Mapped[List[str]] = mapped_column(JSON)  # List of route_ids

    predictions: Mapped[List["ArrivalPrediction"]] = relationship("ArrivalPrediction", back_populates="stop")

class ArrivalPrediction(Base):
    """
    到着予測モデル
    """
    __tablename__ = "arrival_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stop_id: Mapped[str] = mapped_column(String, ForeignKey("transit_stops.stop_id"))
    vehicle_id: Mapped[str] = mapped_column(String, ForeignKey("transit_vehicles.vehicle_id"))
    predicted_arrival: Mapped[datetime] = mapped_column(DateTime)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vehicle: Mapped["TransitVehicle"] = relationship("TransitVehicle", back_populates="predictions")
    stop: Mapped["TransitStop"] = relationship("TransitStop", back_populates="predictions")
