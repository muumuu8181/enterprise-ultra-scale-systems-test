from sqlalchemy import Column, Integer, String, Float, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
import enum

class TrainingAlgorithm(str, enum.Enum):
    PPO = "ppo"
    SAC = "sac"
    TD3 = "td3"
    DQN = "dqn"

class TrainingTask(Base):
    __tablename__ = "training_tasks"
    id = Column(Integer, primary_key=True, index=True)
    sim_id = Column(String, index=True)
    robot_id = Column(String, index=True)
    objective = Column(JSON)
    algorithm = Column(Enum(TrainingAlgorithm))
    max_episodes = Column(Integer)
    reward_history = Column(JSON, default=list)
    current_episode = Column(Integer, default=0)

    policies = relationship("Policy", back_populates="task")

class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("training_tasks.id"))
    neural_network_config = Column(JSON)
    weights_uri = Column(String)
    eval_score = Column(Float, nullable=True)
    checkpoint_episode = Column(Integer)

    task = relationship("TrainingTask", back_populates="policies")

class Curriculum(Base):
    __tablename__ = "curricula"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    task_sequence = Column(JSON)
    auto_advance_threshold = Column(Float)
    current_stage = Column(Integer, default=0)
