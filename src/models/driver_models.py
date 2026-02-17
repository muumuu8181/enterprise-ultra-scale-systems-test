from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from geoalchemy2 import Geometry
from src.core.database import Base
import enum
from datetime import datetime

class VehicleType(str, enum.Enum):
    bicycle = "bicycle"
    scooter = "scooter"
    car = "car"

class DriverStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    delivering = "delivering"

class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(SAEnum(VehicleType))
    current_location = mapped_column(Geometry('POINT', srid=4326), nullable=True)
    status: Mapped[DriverStatus] = mapped_column(SAEnum(DriverStatus), default=DriverStatus.offline)
    rating: Mapped[float] = mapped_column(default=5.0)
    deliveries_today: Mapped[int] = mapped_column(default=0)

    routes = relationship("DeliveryRoute", back_populates="driver")
    earnings = relationship("DriverEarning", back_populates="driver")

class DeliveryRoute(Base):
    __tablename__ = "delivery_routes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    pickup_location = mapped_column(Geometry('POINT', srid=4326))
    dropoff_location = mapped_column(Geometry('POINT', srid=4326))
    distance_km: Mapped[float]
    estimated_min: Mapped[float]
    actual_duration_min: Mapped[float] = mapped_column(nullable=True)

    driver = relationship("Driver", back_populates="routes")

class DriverEarning(Base):
    __tablename__ = "driver_earnings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    date: Mapped[datetime] = mapped_column(Date)
    deliveries_count: Mapped[int] = mapped_column(default=0)
    base_pay: Mapped[float] = mapped_column(default=0.0)
    tips: Mapped[float] = mapped_column(default=0.0)
    bonuses: Mapped[float] = mapped_column(default=0.0)
    net_earnings: Mapped[float] = mapped_column(default=0.0)

    driver = relationship("Driver", back_populates="earnings")
