from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.models.base import Base

class VaccinationCampaign(Base):
    __tablename__ = 'vaccination_campaigns'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    target_population = Column(Integer)
    vaccine_type = Column(String)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    doses_administered = Column(Integer, default=0)
    coverage_pct = Column(Float, default=0.0)

class AppointmentSlot(Base):
    __tablename__ = 'appointment_slots'

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    date = Column(DateTime(timezone=True))
    time = Column(String)
    vaccine_type = Column(String)
    available = Column(Boolean, default=True)
    booked_patient_id = Column(String, nullable=True)

class OutreachEvent(Base):
    __tablename__ = 'outreach_events'

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('vaccination_campaigns.id'))
    location = Column(Geometry('POINT'))
    event_date = Column(DateTime(timezone=True))
    doses_available = Column(Integer)
    walk_in_allowed = Column(Boolean, default=False)

    campaign = relationship("VaccinationCampaign")
