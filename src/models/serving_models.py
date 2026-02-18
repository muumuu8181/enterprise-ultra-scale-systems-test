from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.core.database import Base

class InferenceEndpoint(Base):
    __tablename__ = "inference_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True)
    endpoint_url = Column(String)
    auth_type = Column(String) # e.g. "api_key", "oauth2"
    latency_p99_ms = Column(Float)
    throughput_rps = Column(Float)
    cost_per_1k = Column(Float)

    logs = relationship("PredictionLog", back_populates="endpoint")
    reports = relationship("ModelMonitorReport", back_populates="endpoint")

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("inference_endpoints.id"))
    request_id = Column(String, index=True)
    input_hash = Column(String)
    prediction = Column(String) # JSON string or similar
    confidence = Column(Float)
    latency_ms = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    endpoint = relationship("InferenceEndpoint", back_populates="logs")

class ModelMonitorReport(Base):
    __tablename__ = "model_monitor_reports"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("inference_endpoints.id"))
    period = Column(String) # e.g. "2023-10-01" or "daily"
    drift_score = Column(Float)
    accuracy_estimate = Column(Float)
    outlier_rate = Column(Float)
    alert_triggered = Column(Boolean, default=False)

    endpoint = relationship("InferenceEndpoint", back_populates="reports")
