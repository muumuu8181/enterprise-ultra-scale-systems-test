from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.rl_models import TrainingTask, Policy, Curriculum
from src.worker import app as celery_app
import random
import asyncio

class TrainingMetrics(BaseModel):
    episode: int
    reward: float
    loss: float
    sim_time: float

class EvalResult(BaseModel):
    mean_reward: float
    std_reward: float
    episodes: int

async def run_training_step(task_id: int, db: AsyncSession) -> TrainingMetrics:
    result = await db.execute(select(TrainingTask).where(TrainingTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # Simulate training
    await asyncio.sleep(0.1) # Mock computation

    current_episode = task.current_episode + 1
    reward = random.uniform(-10, 10)
    loss = random.uniform(0, 1)

    task.current_episode = current_episode
    # Ensure JSON field is treated as list and updated
    history = list(task.reward_history) if task.reward_history else []
    history.append(reward)
    task.reward_history = history

    await db.commit()
    await db.refresh(task)

    return TrainingMetrics(
        episode=current_episode,
        reward=reward,
        loss=loss,
        sim_time=0.1
    )

async def evaluate_policy(policy_id: int, n_episodes: int, db: AsyncSession) -> EvalResult:
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalars().first()
    if not policy:
        raise ValueError(f"Policy {policy_id} not found")

    # Simulate evaluation
    await asyncio.sleep(0.5)

    rewards = [random.uniform(0, 100) for _ in range(n_episodes)]
    mean_reward = sum(rewards) / n_episodes
    std_reward = (sum([(r - mean_reward)**2 for r in rewards]) / n_episodes) ** 0.5

    policy.eval_score = mean_reward
    await db.commit()
    await db.refresh(policy)

    return EvalResult(
        mean_reward=mean_reward,
        std_reward=std_reward,
        episodes=n_episodes
    )

async def generate_curriculum(difficulty_curve: str) -> Curriculum:
    # Mock logic
    task_sequence = []
    if difficulty_curve == "linear":
        task_sequence = [{"stage": i, "difficulty": round(i * 0.1, 2)} for i in range(10)]
    elif difficulty_curve == "exponential":
        task_sequence = [{"stage": i, "difficulty": round(2**i * 0.01, 2)} for i in range(10)]
    else:
        task_sequence = [{"stage": 1, "difficulty": 0.5}]

    # Note: This returns a transient object, usually caller will add to session
    return Curriculum(
        name=f"Generated {difficulty_curve}",
        task_sequence=task_sequence,
        auto_advance_threshold=0.8,
        current_stage=0
    )
