import pytest
from fastapi.testclient import TestClient
from src.api.v1.network import router
from fastapi import FastAPI
from src.models.network_models import NetworkElement, ServiceOrder, FaultTicket, NetworkElementType
from src.services.provisioning_telco import provision_service, configure_network_element, run_acceptance_test

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_models_exist():
    assert NetworkElement.__tablename__ == "network_elements"
    assert ServiceOrder.__tablename__ == "service_orders"
    assert FaultTicket.__tablename__ == "fault_tickets"
    assert NetworkElementType.enodeB == "enodeB"

def test_services_import():
    assert callable(provision_service)
    assert callable(configure_network_element)
    assert callable(run_acceptance_test)

def test_api_health():
    response = client.get("/network/elements/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_capacity():
    response = client.get("/network/capacity-report")
    assert response.status_code == 200
    assert "total_capacity_mbps" in response.json()

def test_api_post_fault_ticket():
    ticket_data = {
        "ne_id": 1,
        "fault_type": "power_failure",
        "severity": "P1",
        "status": "open",
        "mttr_hours": None
    }
    response = client.post("/fault-tickets", json=ticket_data)
    assert response.status_code == 200
    data = response.json()
    assert data["fault_type"] == "power_failure"
    assert "id" in data

def test_api_service_status():
    response = client.get("/service-orders/123/status")
    assert response.status_code == 200
    assert response.json()["id"] == 123
