from sqlalchemy import Column, Integer, String, Enum as SAEnum, JSON, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
import enum
import datetime

Base = declarative_base()

class EntityType(str, enum.Enum):
    USER = "user"
    ITEM = "item"
    SESSION = "session"

class StorageType(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BOTH = "both"

class FeatureDType(str, enum.Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    EMBEDDING = "embedding"

class FeatureGroup(Base):
    __tablename__ = 'feature_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    entity_type = Column(SAEnum(EntityType), nullable=False)
    storage_type = Column(SAEnum(StorageType), nullable=False)
    tags = Column(JSON, default={})

    features = relationship("Feature", back_populates="group")

class Feature(Base):
    __tablename__ = 'features'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('feature_groups.id'), nullable=False)
    name = Column(String, index=True, nullable=False)
    dtype = Column(SAEnum(FeatureDType), nullable=False)
    transformation_logic = Column(String, nullable=True)
    version = Column(String, default="v1")
    lineage = Column(JSON, default={})

    group = relationship("FeatureGroup", back_populates="features")

class FeatureView(Base):
    __tablename__ = 'feature_views'

    id = Column(Integer, primary_key=True, index=True)
    features = Column(JSON, nullable=False) # List of feature names or IDs
    source_query = Column(String, nullable=False)
    freshness_minutes = Column(Integer, nullable=True)
    materialized_at = Column(DateTime(timezone=True), nullable=True)
