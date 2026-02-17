from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.models.v2x_models import Base, utcnow

class MisbehaviorReport(Base):
    """
    Misbehavior Report model for V2X cybersecurity.

    Attributes:
        id (int): Report ID
        vehicle_id (str): ID of the vehicle reported for misbehavior
        attack_type (str): Type of attack (e.g., spoofing, replay, sybil)
        evidence (dict): JSON evidence data supporting the report
        trust_impact (float): Impact on the vehicle's trust score
        reporter_id (str): ID of the entity reporting the misbehavior
        reported_at (datetime): Timestamp when the report was created
    """
    __tablename__ = "misbehavior_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, index=True)
    attack_type: Mapped[str] = mapped_column(String)
    evidence: Mapped[dict] = mapped_column(JSON)
    trust_impact: Mapped[float] = mapped_column(Float)
    reporter_id: Mapped[str] = mapped_column(String)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
