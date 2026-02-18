import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
from src.api.v1.customers import router
from src.models.telco_models import Customer, Service, CDRRecord, CustomerType, ServiceType, CallType
from src.services.billing_telco import rate_cdr, generate_bill, calculate_revenue_by_plan, Bill

app = FastAPI()
app.include_router(router)
client = TestClient(app)

# --- Model Tests ---
def test_customer_model():
    customer = Customer(
        name="John Doe",
        customer_type=CustomerType.PREPAID,
        account_status="active",
        credit_score=700
    )
    assert customer.name == "John Doe"
    assert customer.customer_type == CustomerType.PREPAID

def test_service_model():
    service = Service(
        service_type=ServiceType.MOBILE,
        plan_id="plan_1",
        status="active"
    )
    assert service.service_type == ServiceType.MOBILE

def test_cdr_model():
    cdr = CDRRecord(
        call_type=CallType.VOICE,
        source="123",
        destination="456",
        duration=60
    )
    assert cdr.call_type == CallType.VOICE

# --- API Tests ---
def test_onboard_customer():
    response = client.post("/customers/onboard", json={
        "name": "Jane Doe",
        "customer_type": "postpaid",
        "credit_score": 750
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["customer_type"] == "postpaid"

def test_get_customer_services():
    response = client.get("/customers/1/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "service_type" in data[0]

def test_get_customer_bill():
    response = client.get("/customers/1/bill")
    assert response.status_code == 200
    data = response.json()
    assert "total_amount" in data

def test_plan_change():
    response = client.post("/customers/1/plan-change", json={
        "service_id": 101,
        "new_plan_id": "plan_gold"
    })
    assert response.status_code == 200

def test_suspend_customer():
    response = client.post("/customers/1/suspend", json={
        "reason": "non-payment"
    })
    assert response.status_code == 200

def test_usage_history():
    response = client.get("/customers/1/usage-history")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data

# --- Service Tests ---
@pytest.mark.asyncio
async def test_rate_cdr():
    cdr = CDRRecord(call_type=CallType.VOICE, duration=60)
    cost = await rate_cdr(cdr)
    assert cost == 0.60

    cdr_data = CDRRecord(call_type=CallType.DATA, bytes=1048576) # 1 MB
    cost_data = await rate_cdr(cdr_data)
    assert cost_data == 0.10

@pytest.mark.asyncio
async def test_generate_bill():
    bill = await generate_bill(1, "2023-10")
    assert isinstance(bill, Bill)
    assert bill.total_amount > 0

@pytest.mark.asyncio
async def test_calculate_revenue():
    rev = await calculate_revenue_by_plan("plan_x", "2023-10")
    assert rev > 0
