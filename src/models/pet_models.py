import enum
from datetime import date
from typing import List, Optional, Any

from sqlalchemy import String, Integer, Date, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class Species(str, enum.Enum):
    dog = "dog"
    cat = "cat"
    bird = "bird"
    rabbit = "rabbit"

class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    species: Mapped[Species] = mapped_column(Enum(Species))
    breed: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    birthdate: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[float] = mapped_column(Float)
    microchip_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)

    visits: Mapped[List["VetVisit"]] = relationship("VetVisit", back_populates="pet")
    vaccinations: Mapped[List["Vaccination"]] = relationship("Vaccination", back_populates="pet")

class VetVisit(Base):
    __tablename__ = "vet_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    vet_id: Mapped[int] = mapped_column(Integer)
    visit_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(String)
    diagnosis: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prescriptions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    next_visit: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    pet: Mapped["Pet"] = relationship("Pet", back_populates="visits")

class Vaccination(Base):
    __tablename__ = "vaccinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    vaccine_name: Mapped[str] = mapped_column(String)
    administered_date: Mapped[date] = mapped_column(Date)
    batch_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    next_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vet_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    pet: Mapped["Pet"] = relationship("Pet", back_populates="vaccinations")
