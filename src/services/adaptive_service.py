from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.learning_models import LearnerProfile, LearningPath, Assessment
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timezone

class Question(BaseModel):
    id: str
    text: str
    difficulty: float
    options: List[str]
    correct_option: int # Index of correct option

async def generate_learning_path(db: AsyncSession, learner_id: int, goal: str) -> LearningPath:
    """
    Generates a personalized learning path for a learner based on their goal.
    """
    # Check if learner exists (optional, validation)
    result = await db.execute(select(LearnerProfile).where(LearnerProfile.id == learner_id))
    learner = result.scalar_one_or_none()

    # Mock logic for module generation
    # In a real system, this would analyze the goal and learner profile
    modules = [
        {"id": "mod_intro", "name": f"Introduction to {goal}", "difficulty": 0.3, "topics": ["basics", "history"]},
        {"id": "mod_inter", "name": f"Intermediate {goal}", "difficulty": 0.6, "topics": ["concepts", "practice"]},
        {"id": "mod_adv", "name": f"Advanced {goal}", "difficulty": 0.9, "topics": ["advanced", "project"]}
    ]

    new_path = LearningPath(
        learner_id=learner_id,
        goal=goal,
        modules=modules,
        current_module="mod_intro",
        completion_pct=0.0,
        adaptive_adjusted_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(new_path)
    await db.commit()
    await db.refresh(new_path)
    return new_path

async def select_next_question(db: AsyncSession, assessment_id: int, learner_id: int) -> Question:
    """
    Selects the next question based on Item Response Theory (IRT).
    """
    # Verify assessment exists
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()

    # Mock IRT Logic
    # 1. Fetch learner ability (theta) from profile or recent performance
    # 2. Fetch available questions for the module
    # 3. Select question that maximizes Information Function at learner's theta

    # Returning a mock question
    return Question(
        id=f"q_{int(datetime.now(timezone.utc).timestamp())}",
        text="What is the primary benefit of Adaptive Learning?",
        difficulty=0.5,
        options=[
            "It is faster for everyone",
            "It personalizes content to learner needs",
            "It is cheaper to implement",
            "It requires no internet"
        ],
        correct_option=1
    )

async def update_knowledge_graph(db: AsyncSession, learner_id: int, assessment_result: dict):
    """
    Updates the learner's knowledge graph based on assessment results.
    """
    result = await db.execute(select(LearnerProfile).where(LearnerProfile.id == learner_id))
    learner = result.scalar_one_or_none()

    if learner:
        current_graph = dict(learner.knowledge_graph) if learner.knowledge_graph else {}

        # Example update logic
        topics = assessment_result.get("topics", [])
        score = assessment_result.get("score", 0.0) # 0.0 to 1.0

        for topic in topics:
            current_level = current_graph.get(topic, 0.0)
            # Simple update rule: move 10% towards the new score
            new_level = current_level + 0.1 * (score - current_level)
            current_graph[topic] = round(new_level, 2)

        learner.knowledge_graph = current_graph

        # Also update strengths/weaknesses
        strengths = learner.strengths or []
        weaknesses = learner.weaknesses or []

        # Naive categorization
        for topic, level in current_graph.items():
            if level > 0.8 and topic not in strengths:
                strengths.append(topic)
                if topic in weaknesses:
                    weaknesses.remove(topic)
            elif level < 0.4 and topic not in weaknesses:
                weaknesses.append(topic)
                if topic in strengths:
                    strengths.remove(topic)

        learner.strengths = strengths
        learner.weaknesses = weaknesses

        await db.commit()
        await db.refresh(learner)
