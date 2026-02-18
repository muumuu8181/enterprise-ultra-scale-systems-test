from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, Enum
from src.core.database import Base
import enum

class StreamType(str, enum.Enum):
    VIDEO = "video"
    SENSOR = "sensor"
    LOG = "log"

class ProcessingMode(str, enum.Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"

class EdgeDataStream(Base):
    __tablename__ = "edge_data_streams"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    stream_type = Column(Enum(StreamType), nullable=False)
    ingestion_rate = Column(Float)  # e.g., MB/s or events/s
    processing_mode = Column(Enum(ProcessingMode), default=ProcessingMode.LOCAL)

class LocalInference(Base):
    __tablename__ = "local_inferences"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    model_id = Column(String)
    inference_latency_ms = Column(Float)
    result = Column(JSON)
    sent_to_cloud = Column(Boolean, default=False)

class DataPolicy(Base):
    __tablename__ = "data_policies"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    retention_days = Column(Integer)
    compression_ratio = Column(Float)
    sync_to_cloud_pct = Column(Float)
    privacy_filter_rules = Column(JSON)
