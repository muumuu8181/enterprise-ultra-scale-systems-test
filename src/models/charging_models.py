from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
import enum
from datetime import datetime, timezone

Base = declarative_base()

class StationType(enum.Enum):
    PUBLIC = "public"
    WORKPLACE = "workplace"
    RESIDENTIAL = "residential"

class StationStatus(enum.Enum):
    OPEN = "open"
    LIMITED = "limited"
    CLOSED = "closed"

class ConnectorType(enum.Enum):
    CCS = "ccs"
    CHADEMO = "chademo"
    TYPE2 = "type2"
    TESLA = "tesla"

class ChargerStatus(enum.Enum):
    AVAILABLE = "available"
    CHARGING = "charging"
    FAULTED = "faulted"
    OFFLINE = "offline"

class PaymentMethod(enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    APP_PAYMENT = "app_payment"
    RFID_CARD = "rfid_card"

class ChargingStation(Base):
    __tablename__ = 'charging_stations'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)  # GeoJSON support via geoalchemy2
    operator_id = Column(String, nullable=False)
    charger_count = Column(Integer, default=0)
    station_type = Column(Enum(StationType), nullable=False)
    amenities = Column(JSON, nullable=True)
    status = Column(Enum(StationStatus), default=StationStatus.OPEN)

    chargers = relationship("Charger", back_populates="station")

class Charger(Base):
    __tablename__ = 'chargers'

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('charging_stations.id'), nullable=False)
    connector_type = Column(Enum(ConnectorType), nullable=False)
    power_kw = Column(Float, nullable=False)
    status = Column(Enum(ChargerStatus), default=ChargerStatus.AVAILABLE)
    firmware_version = Column(String, nullable=True)

    station = relationship("ChargingStation", back_populates="chargers")
    sessions = relationship("ChargingSession", back_populates="charger")

class ChargingSession(Base):
    __tablename__ = 'charging_sessions'

    id = Column(Integer, primary_key=True)
    charger_id = Column(Integer, ForeignKey('chargers.id'), nullable=False)
    user_id = Column(String, nullable=False)
    vehicle_id = Column(String, nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    energy_kwh = Column(Float, default=0.0)
    peak_power_kw = Column(Float, nullable=True)
    cost = Column(Float, default=0.0)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    soc_start_pct = Column(Float, nullable=True)
    soc_end_pct = Column(Float, nullable=True)

    charger = relationship("Charger", back_populates="sessions")
