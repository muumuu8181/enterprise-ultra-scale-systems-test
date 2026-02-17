from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timezone

from src.models.robot_models import (
    Robot, RobotTask, RobotStatus, RobotType, TaskType, Assignment,
    RobotRead, TaskCreate, TaskRead, RobotCreate
)
from src.services.fleet_manager import dispatch_task, optimize_robot_paths

# Simple DB dependency placeholder
# In a real app, this would be in src.core.database or similar.
# The test suite will override this dependency.
async def get_db():
    raise NotImplementedError("Database dependency not configured")

router = APIRouter()

@router.get("/robots/fleet/status", response_model=List[RobotRead])
async def get_fleet_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Robot))
    return result.scalars().all()

@router.post("/robots/{robot_id}/assign-task", response_model=RobotRead)
async def assign_task_to_specific_robot(
    robot_id: int,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually assign a task to a specific robot.
    """
    # Fetch robot
    result = await db.execute(select(Robot).where(Robot.id == robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    if robot.status != RobotStatus.IDLE:
        raise HTTPException(status_code=400, detail="Robot is not idle")

    # Create task
    new_task = RobotTask(
        task_type=task_data.task_type,
        priority=task_data.priority,
        payload=task_data.payload,
        robot_id=robot.id,
        started_at=datetime.now(timezone.utc)
    )
    db.add(new_task)

    # Update robot
    robot.status = RobotStatus.WORKING
    # We need to flush to get new_task.id
    await db.flush()
    robot.current_task_id = new_task.id

    await db.commit()
    await db.refresh(robot)
    return robot

@router.post("/robots/{robot_id}/emergency-stop", response_model=RobotRead)
async def emergency_stop(robot_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Robot).where(Robot.id == robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    robot.status = RobotStatus.ERROR
    # If there was a task, we might want to mark it as failed or interrupted.
    # For simplicity, we just stop the robot.

    await db.commit()
    await db.refresh(robot)
    return robot

@router.get("/robots/analytics/utilization")
async def get_utilization(db: AsyncSession = Depends(get_db)):
    # Calculate % of working robots
    total = await db.scalar(select(func.count(Robot.id)))
    if not total:
        return {"utilization_rate": 0.0, "total_robots": 0, "working_robots": 0}

    working = await db.scalar(select(func.count(Robot.id)).where(Robot.status == RobotStatus.WORKING))
    return {"utilization_rate": round(working / total, 2), "total_robots": total, "working_robots": working}

@router.post("/tasks/optimize-dispatch", response_model=List[Assignment])
async def optimize_tasks(
    tasks: List[TaskCreate],
    db: AsyncSession = Depends(get_db)
):
    # Create transient or persisted tasks
    task_objects = [
        RobotTask(
            task_type=t.task_type,
            priority=t.priority,
            payload=t.payload
        )
        for t in tasks
    ]

    # Persist them so they have IDs for the assignment
    for t in task_objects:
        db.add(t)
    await db.flush()

    assignments = await optimize_robot_paths(db, task_objects)

    # In a real system, we might apply these assignments immediately.
    # Here we just return the plan.

    return assignments
