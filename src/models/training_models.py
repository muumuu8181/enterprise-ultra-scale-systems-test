from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class TrainingDataset(Base):
    __tablename__ = "training_datasets"

    id = Column(Integer, primary_key=True, index=True)
    feature_view_id = Column(String, index=True, nullable=False)
    label_source = Column(String, nullable=False)
    train_size = Column(Float)
    val_size = Column(Float)
    test_size = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    snapshot_path = Column(String, nullable=False)

class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, index=True, nullable=False)
    feature_dataset_id = Column(Integer, ForeignKey("training_datasets.id"), nullable=False)
    hyperparams = Column(JSON)
    metrics = Column(JSON)
    artifacts = Column(JSON)
    status = Column(String, nullable=False)

    training_dataset = relationship("TrainingDataset")

class ModelLineage(Base):
    __tablename__ = "model_lineage"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True, nullable=False)
    training_dataset_id = Column(Integer, ForeignKey("training_datasets.id"), nullable=False)
    feature_group_ids = Column(JSON)
    upstream_models = Column(JSON)

    training_dataset = relationship("TrainingDataset")
