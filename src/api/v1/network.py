from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from datetime import datetime

from src.models.network_models import (
    NetworkElementResponse, NetworkElementCreate,
    ServiceOrderResponse, ServiceOrderCreate,
    FaultTicketResponse, FaultTicketCreate,
    NetworkElementType, OrderType, FaultSeverity, OrderStatus, FaultStatus
)
from src.services.provisioning_telco import (
    provision_service, run_acceptance_test, ProvisionResult, TestResult
)

router = APIRouter()

# Mock Data Store (In-memory for now as we don't have DB session setup yet)
network_elements_db = []
service_orders_db = []
fault_tickets_db = []

@router.get("/network/elements/health")
async def get_network_health():
    # Mock health check
    return {"status": "healthy", "elements_checked": len(network_elements_db), "details": "All systems operational"}

@router.get("/network/capacity-report")
async def get_capacity_report():
    # Mock capacity report
    return {
        "total_capacity_mbps": 100000.0,
        "used_capacity_mbps": 45000.0,
        "utilization_pct": 45.0,
        "regions": [
            {"region": "us-east", "utilization_pct": 60.0},
            {"region": "us-west", "utilization_pct": 30.0}
        ]
    }

@router.post("/fault-tickets", response_model=FaultTicketResponse)
async def create_fault_ticket(ticket: FaultTicketCreate):
    new_ticket_data = ticket.model_dump()
    new_ticket_data["id"] = len(fault_tickets_db) + 1
    # Ensure enums are converted to values if needed, or pydantic handles it.
    # For simplicity in mock, just return as is.
    fault_tickets_db.append(new_ticket_data)
    return new_ticket_data

@router.get("/fault-tickets/{id}/timeline")
async def get_fault_ticket_timeline(id: int):
    # Mock timeline
    return {
        "ticket_id": id,
        "events": [
            {"timestamp": datetime.now().isoformat(), "event": "Ticket Created"},
            {"timestamp": datetime.now().isoformat(), "event": "Assigned to Engineer"},
            {"timestamp": datetime.now().isoformat(), "event": "Investigating"},
        ]
    }

@router.get("/service-orders/{id}/status", response_model=ServiceOrderResponse)
async def get_service_order_status(id: int):
    # Mock status return
    return ServiceOrderResponse(
        id=id,
        customer_id="CUST-001",
        order_type=OrderType.new,
        service_id="SERV-101",
        status=OrderStatus.in_progress,
        workflow_steps={"step1": "completed", "step2": "running"}
    )

@router.post("/service-orders/{id}/provision", response_model=ProvisionResult)
async def provision_service_order(id: int, background_tasks: BackgroundTasks):
    # Trigger provisioning
    result = await provision_service(id)
    return result
