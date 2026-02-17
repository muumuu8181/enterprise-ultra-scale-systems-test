from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, Date, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
import enum
from datetime import datetime, date
from ..database import Base

class DietType(str, enum.Enum):
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"

class ConservationStatus(str, enum.Enum):
    LC = "LC"
    NT = "NT"
    VU = "VU"
    EN = "EN"
    CR = "CR"

class Biome(str, enum.Enum):
    TROPICAL = "tropical"
    ARCTIC = "arctic"
    SAVANNA = "savanna"
    AQUATIC = "aquatic"

class RecordType(str, enum.Enum):
    CHECKUP = "checkup"
    TREATMENT = "treatment"
    SURGERY = "surgery"
    VACCINATION = "vaccination"

class Enclosure(Base):
    __tablename__ = "enclosures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    biome: Mapped[Biome] = mapped_column(SQLEnum(Biome), nullable=False)
    area_sq_m: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_range: Mapped[Optional[str]] = mapped_column(String)
    humidity_range: Mapped[Optional[str]] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer)
    current_count: Mapped[int] = mapped_column(Integer, default=0)
    maintenance_schedule: Mapped[Optional[dict]] = mapped_column(JSON)

    animals: Mapped[List["Animal"]] = relationship("Animal", back_populates="enclosure")

class Animal(Base):
    __tablename__ = "animals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    species: Mapped[str] = mapped_column(String, nullable=False)
    genus: Mapped[Optional[str]] = mapped_column(String)
    enclosure_id: Mapped[int] = mapped_column(ForeignKey("enclosures.id"))
    sex: Mapped[Optional[str]] = mapped_column(String)
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    diet_type: Mapped[Optional[DietType]] = mapped_column(SQLEnum(DietType))
    conservation_status: Mapped[Optional[ConservationStatus]] = mapped_column(SQLEnum(ConservationStatus))
    studbook_number: Mapped[Optional[str]] = mapped_column(String)

    enclosure: Mapped["Enclosure"] = relationship("Enclosure", back_populates="animals")
    medical_records: Mapped[List["VeterinaryRecord"]] = relationship("VeterinaryRecord", back_populates="animal")

class VeterinaryRecord(Base):
    __tablename__ = "veterinary_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animals.id"))
    vet_id: Mapped[Optional[str]] = mapped_column(String)
    record_type: Mapped[RecordType] = mapped_column(SQLEnum(RecordType), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    diagnosis: Mapped[Optional[str]] = mapped_column(String)
    medications: Mapped[Optional[dict]] = mapped_column(JSON)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    next_followup: Mapped[Optional[datetime]] = mapped_column(DateTime)

    animal: Mapped["Animal"] = relationship("Animal", back_populates="medical_records")
