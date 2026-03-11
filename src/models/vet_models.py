from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
import enum
from src.database import Base

class Species(str, enum.Enum):
    dog = "dog"
    cat = "cat"
    bird = "bird"
    reptile = "reptile"
    small_mammal = "small_mammal"

class PetStatus(str, enum.Enum):
    active = "active"
    deceased = "deceased"

class AppointmentType(str, enum.Enum):
    checkup = "checkup"
    vaccination = "vaccination"
    surgery = "surgery"
    emergency = "emergency"
    dental = "dental"

class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    checked_in = "checked_in"
    in_progress = "in_progress"
    completed = "completed"
    no_show = "no_show"

class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    species = Column(Enum(Species), nullable=False)
    breed = Column(String)
    sex = Column(String)  # M/F/Neutered/Spayed
    birth_date = Column(Date)
    weight_kg = Column(Float)
    microchip_id = Column(String, unique=True, index=True)
    owner_id = Column(String, index=True)  # External owner ID
    allergies = Column(JSON, default=list)
    status = Column(Enum(PetStatus), default=PetStatus.active)

    appointments = relationship("Appointment", back_populates="pet")
    medical_records = relationship("MedicalRecord", back_populates="pet")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    vet_id = Column(String, index=True)  # External vet ID
    appointment_type = Column(Enum(AppointmentType), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_min = Column(Integer)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled)
    notes = Column(String)

    pet = relationship("Pet", back_populates="appointments")
    medical_record = relationship("MedicalRecord", back_populates="appointment", uselist=False)

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True)
    diagnosis = Column(String)
    treatments = Column(JSON, default=list)
    prescriptions = Column(JSON, default=list)
    lab_results = Column(JSON, default=dict)
    vitals = Column(JSON, default=dict)
    next_followup = Column(Date)

    pet = relationship("Pet", back_populates="medical_records")
    appointment = relationship("Appointment", back_populates="medical_record")
