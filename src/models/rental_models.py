from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from src.core.database import Base
from datetime import datetime
import enum

class VehicleCategory(str, enum.Enum):
    ECONOMY = "economy"
    LUXURY = "luxury"
    SUV = "suv"

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    make: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    license_plate: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    category: Mapped[VehicleCategory] = mapped_column(SAEnum(VehicleCategory), nullable=False)
    daily_rate: Mapped[float] = mapped_column(Float, nullable=False)
    location = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(SAEnum(VehicleStatus), default=VehicleStatus.AVAILABLE)

    bookings = relationship("RentalBooking", back_populates="vehicle")

class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    PENDING = "pending"

class RentalBooking(Base):
    __tablename__ = "rental_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    renter_id: Mapped[int] = mapped_column(Integer, nullable=False) # Assuming renter comes from another service/table
    pickup_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    return_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pickup_location = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), default=BookingStatus.PENDING)

    vehicle = relationship("Vehicle", back_populates="bookings")
    driving_record = relationship("DrivingRecord", back_populates="booking", uselist=False)
    insurance = relationship("Insurance", back_populates="booking", uselist=False)

class DrivingRecord(Base):
    __tablename__ = "driving_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("rental_bookings.id"), unique=True, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    avg_speed: Mapped[float] = mapped_column(Float, nullable=False)
    harsh_braking_count: Mapped[int] = mapped_column(Integer, default=0)
    fuel_level_end: Mapped[float] = mapped_column(Float, nullable=False) # Percentage 0-100?

    booking = relationship("RentalBooking", back_populates="driving_record")

class InsuranceType(str, enum.Enum):
    BASIC = "basic"
    FULL = "full"

class Insurance(Base):
    __tablename__ = "insurances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("rental_bookings.id"), unique=True, nullable=False)
    type: Mapped[InsuranceType] = mapped_column(SAEnum(InsuranceType), nullable=False)
    deductible: Mapped[float] = mapped_column(Float, nullable=False)
    premium: Mapped[float] = mapped_column(Float, nullable=False)

    booking = relationship("RentalBooking", back_populates="insurance")
