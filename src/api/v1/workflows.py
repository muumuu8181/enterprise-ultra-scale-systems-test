from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from src.models.workflow_models import TriggerType, WorkflowStatus, StepStatus, StepType

router = APIRouter()

# Pydantic Schemas

class WorkflowStepDefinition(BaseModel):
    step_name: str
    step_type: StepType
    config: Dict[str, Any]

class WorkflowDefinitionCreate(BaseModel):
    name: str
    trigger_type: TriggerType
    steps: List[Dict[str, Any]]
    error_handling: Optional[Dict[str, Any]] = None

class WorkflowDefinitionResponse(BaseModel):
    id: int
    name: str
    version: int
    trigger_type: TriggerType
    steps: List[Dict[str, Any]]
    error_handling: Optional[Dict[str, Any]]

class WorkflowTriggerRequest(BaseModel):
    input_data: Dict[str, Any]

class WorkflowInstanceResponse(BaseModel):
    id: int
    definition_id: int
    triggered_by: str
    status: WorkflowStatus
    current_step: Optional[str]
    started_at: datetime
    context: Dict[str, Any]

class WorkflowStepResponse(BaseModel):
    id: int
    instance_id: int
    step_name: str
    step_type: StepType
    input: Optional[Dict[str, Any]]
    output: Optional[Dict[str, Any]]
    status: StepStatus

class WorkflowRetryRequest(BaseModel):
    from_step_id: int

# Endpoints

@router.post("/workflows/define", response_model=WorkflowDefinitionResponse)
async def define_workflow(workflow: WorkflowDefinitionCreate):
    # Mock response
    return WorkflowDefinitionResponse(
        id=1,
        name=workflow.name,
        version=1,
        trigger_type=workflow.trigger_type,
        steps=workflow.steps,
        error_handling=workflow.error_handling
    )

@router.get("/workflows/{id}/versions", response_model=List[WorkflowDefinitionResponse])
async def get_workflow_versions(id: int):
    # Mock response
    return [
        WorkflowDefinitionResponse(
            id=id,
            name="Mock Workflow",
            version=1,
            trigger_type=TriggerType.MANUAL,
            steps=[],
            error_handling={}
        )
    ]

@router.post("/workflows/{id}/trigger", response_model=WorkflowInstanceResponse)
async def trigger_workflow(id: int, request: WorkflowTriggerRequest):
    # Mock response
    return WorkflowInstanceResponse(
        id=100,
        definition_id=id,
        triggered_by="api",
        status=WorkflowStatus.RUNNING,
        current_step="step-1",
        started_at=datetime.now(timezone.utc),
        context=request.input_data
    )

@router.get("/instances/{id}/status", response_model=WorkflowInstanceResponse)
async def get_instance_status(id: int):
    return WorkflowInstanceResponse(
        id=id,
        definition_id=1,
        triggered_by="api",
        status=WorkflowStatus.RUNNING,
        current_step="step-2",
        started_at=datetime.now(timezone.utc),
        context={}
    )

@router.get("/instances/{id}/steps", response_model=List[WorkflowStepResponse])
async def get_instance_steps(id: int):
    return [
        WorkflowStepResponse(
            id=1,
            instance_id=id,
            step_name="step-1",
            step_type=StepType.HTTP,
            input={},
            output={},
            status=StepStatus.COMPLETED
        )
    ]

@router.post("/instances/{id}/retry", response_model=WorkflowInstanceResponse)
async def retry_instance(id: int, request: WorkflowRetryRequest):
    # Utilizing service logic here would be ideal, but for now mocking
    return WorkflowInstanceResponse(
        id=id,
        definition_id=1,
        triggered_by="retry",
        status=WorkflowStatus.RUNNING,
        current_step=str(request.from_step_id),
        started_at=datetime.now(timezone.utc),
        context={}
    )
