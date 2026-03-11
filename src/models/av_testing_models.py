from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Enum as SqEnum
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class ScenarioType(str, enum.Enum):
    highway = "highway"
    urban = "urban"
    parking = "parking"
    weather = "weather"

class TestResult(str, enum.Enum):
    pass_result = "pass"
    fail = "fail"
    inconclusive = "inconclusive"

class MetricType(str, enum.Enum):
    ttc = "ttc"
    pet = "pet"
    jerk = "jerk"
    lane_deviation = "lane_deviation"

class TestScenario(Base):
    __tablename__ = 'test_scenarios'

    id = Column(Integer, primary_key=True, index=True)
    scenario_type = Column(SqEnum(ScenarioType), nullable=False)
    description = Column(String, nullable=True)
    environment_config = Column(JSON, nullable=True)
    expected_behavior = Column(String, nullable=True)
    difficulty_level = Column(String, nullable=True)
    regulatory_standard = Column(String, nullable=True)

    test_runs = relationship("TestRun", back_populates="scenario")

class TestRun(Base):
    __tablename__ = 'test_runs'

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey('test_scenarios.id'))
    vehicle_id = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    distance_km = Column(Float, nullable=True)
    interventions_count = Column(Integer, default=0)
    disengagements = Column(JSON, nullable=True)
    result = Column(SqEnum(TestResult), nullable=True)
    log_uri = Column(String, nullable=True)

    scenario = relationship("TestScenario", back_populates="test_runs")
    metrics = relationship("SafetyMetric", back_populates="test_run")

class SafetyMetric(Base):
    __tablename__ = 'safety_metrics'

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey('test_runs.id'))
    metric_type = Column(SqEnum(MetricType), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(JSON, nullable=True) # GeoJSON

    test_run = relationship("TestRun", back_populates="metrics")
