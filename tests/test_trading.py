import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.v1.trading import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_submit_bid():
    response = client.post("/bids/submit", json={
        "generator_id": 1,
        "volume_mwh": 100.5,
        "min_price": 40.0,
        "max_price": 60.0,
        "delivery_period": "2023-10-27T10:00:00Z"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["generator_id"] == 1
    assert data["status"] == "pending"
    assert "id" in data

def test_get_bid_status():
    # Create a bid first
    response = client.post("/bids/submit", json={
        "generator_id": 2,
        "volume_mwh": 50,
        "min_price": 45.0,
        "max_price": 55.0,
        "delivery_period": "2023-10-27T11:00:00Z"
    })
    bid_id = response.json()["id"]

    response = client.get(f"/bids/{bid_id}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

def test_market_clearing_price():
    # Add some bids
    client.post("/bids/submit", json={
        "generator_id": 3,
        "volume_mwh": 10,
        "min_price": 10,
        "max_price": 50,
        "delivery_period": "now"
    })

    response = client.get("/market/clearing-price")
    assert response.status_code == 200
    assert "clearing_price" in response.json()
    assert isinstance(response.json()["clearing_price"], float)

def test_execute_trades():
    response = client.post("/trades/execute")
    assert response.status_code == 200
    # currently returns empty list
    assert response.json()["executed_trades"] == []

def test_get_trade_settlement():
    response = client.get("/trades/1/settlement")
    assert response.status_code == 200
    data = response.json()
    assert data["trade_id"] == 1
    assert data["status"] == "settled"
