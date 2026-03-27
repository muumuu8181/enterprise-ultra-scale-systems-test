from sqlalchemy import Column, Integer, String, Date, JSON, ForeignKey, Float, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    insurance_id = Column(String)
    current_rx = Column(JSON)
    last_exam_date = Column(Date)
    contact_lens_wearer = Column(Boolean, default=False)
    medical_history = Column(JSON)

class EyeExam(Base):
    __tablename__ = 'eye_exams'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    optometrist_id = Column(Integer)
    exam_date = Column(Date)
    visual_acuity_od = Column(String) # Right Eye
    visual_acuity_os = Column(String) # Left Eye
    sphere_od = Column(Float)
    sphere_os = Column(Float)
    cylinder_od = Column(Float)
    cylinder_os = Column(Float)
    axis_od = Column(Integer)
    axis_os = Column(Integer)
    pupillary_distance = Column(Float)
    iop_od = Column(Float) # Intraocular Pressure
    iop_os = Column(Float)
    notes = Column(String)

class LensType(str, enum.Enum):
    single = "single"
    bifocal = "bifocal"
    progressive = "progressive"
    photochromic = "photochromic"

class OrderStatus(str, enum.Enum):
    ordered = "ordered"
    lab = "lab"
    ready = "ready"
    dispensed = "dispensed"

class FrameOrder(Base):
    __tablename__ = 'frame_orders'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    frame_brand = Column(String)
    frame_model = Column(String)
    lens_type = Column(Enum(LensType))
    lens_material = Column(String)
    coatings = Column(JSON)
    total_price = Column(Float)
    insurance_applied = Column(Boolean)
    status = Column(Enum(OrderStatus))
