import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.models.workflow_models import WorkflowInstance, WorkflowStatus

@dataclass
class StepResult:
    success: bool
    output: Dict[str, Any]
    error: Optional[str] = None

async def execute_step(step_id: int) -> StepResult:
    """
    Executes a workflow step.
    """
    # Logic to fetch step, execute it based on type, update status
    # For now, we'll return a mock result
    await asyncio.sleep(0.1) # Simulate work
    return StepResult(success=True, output={"result": "step_executed", "step_id": step_id}, error=None)

async def evaluate_condition(condition: dict, context: dict) -> bool:
    """
    Evaluates a condition against the workflow context.
    """
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    if field and field in context:
        context_value = context[field]
        if operator == "==":
            return str(context_value) == str(value)
        elif operator == "!=":
            return str(context_value) != str(value)
        elif operator == ">":
            return float(context_value) > float(value)
        elif operator == "<":
            return float(context_value) < float(value)

    return True

async def resume_from_checkpoint(instance_id: int, step_id: int) -> WorkflowInstance:
    """
    Resumes a workflow instance from a specific step/checkpoint.
    """
    # Logic to resume a workflow instance from a specific step
    # In a real app, this would update the DB.

    instance = WorkflowInstance(
        id=instance_id,
        status=WorkflowStatus.RUNNING,
        current_step=str(step_id),
        context={}
    )
    return instance
