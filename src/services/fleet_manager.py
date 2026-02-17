from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.robot_models import Robot, RobotTask, RobotStatus, RobotType, TaskType, Assignment
from datetime import datetime, timezone

async def dispatch_task(db: AsyncSession, task: RobotTask) -> Robot | None:
    """
    Assigns a task to an available robot.
    """
    # 1. Determine required robot type
    required_type = None
    if task.task_type == TaskType.PICK:
        required_type = RobotType.PICKER
    elif task.task_type == TaskType.CARRY:
        required_type = RobotType.CARRIER
    elif task.task_type == TaskType.SORT:
        required_type = RobotType.SORTER
    # CHARGE might be special, handled by any robot or specific logic.

    # 2. Query for idle robots of the required type
    stmt = select(Robot).where(
        Robot.status == RobotStatus.IDLE,
        Robot.battery_pct > 20 # Simple constraint
    )
    if required_type:
        stmt = stmt.where(Robot.robot_type == required_type)

    result = await db.execute(stmt)
    candidates = result.scalars().all()

    if not candidates:
        return None

    # 3. Select best candidate (e.g., highest battery)
    best_robot = max(candidates, key=lambda r: r.battery_pct)

    # 4. Assign
    # Ensure task is persisted to get ID
    if task.id is None:
        db.add(task)
        await db.flush()

    best_robot.status = RobotStatus.WORKING
    best_robot.current_task_id = task.id

    task.robot_id = best_robot.id
    task.started_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(best_robot)
    return best_robot

async def optimize_robot_paths(db: AsyncSession, tasks: list[RobotTask]) -> list[Assignment]:
    """
    Simple optimization: assign pending tasks to available robots.
    Returns a list of assignments but does not commit them to DB.
    """
    assignments = []

    # Fetch all idle robots
    result = await db.execute(select(Robot).where(Robot.status == RobotStatus.IDLE))
    available_robots = list(result.scalars().all())

    assigned_robot_ids = set()

    for task in tasks:
        # Determine type
        required_type = None
        if task.task_type == TaskType.PICK:
            required_type = RobotType.PICKER
        elif task.task_type == TaskType.CARRY:
            required_type = RobotType.CARRIER
        elif task.task_type == TaskType.SORT:
            required_type = RobotType.SORTER

        # Find match
        best_robot = None
        for robot in available_robots:
            if robot.id in assigned_robot_ids:
                continue
            if required_type and robot.robot_type != required_type:
                continue
            if robot.battery_pct < 20:
                continue

            # Simple heuristic: take the first one found
            best_robot = robot
            break

        if best_robot:
            assignments.append(Assignment(robot_id=best_robot.id, task_id=task.id))
            assigned_robot_ids.add(best_robot.id)

    return assignments
