import pytest
from src.models.trading_models import Order, OrderType, OrderSide, OrderStatus, TradingAccount
from src.services import order_service
from src.api.v1.orders import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.mark.asyncio
async def test_place_order_service():
    # Setup
    order = Order(
        id="ord_1",
        account_id="acc_1",
        symbol="AAPL",
        order_type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=10,
        price=150.0
    )

    # Execute
    result = await order_service.place_order("acc_1", order)

    # Verify
    assert result.success is True
    assert result.order.status == OrderStatus.FILLED

    # Check account
    account = order_service.get_account("acc_1")
    assert account is not None
    assert account.balance == 10000.0 - (150.0 * 10)

    # Check positions
    positions = order_service.get_positions("acc_1")
    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == 10

def test_place_order_api():
    order_data = {
        "id": "ord_2",
        "account_id": "acc_2",
        "symbol": "GOOG",
        "order_type": "market",
        "side": "buy",
        "quantity": 5,
        "price": 200.0,
        "status": "pending"
    }

    response = client.post("/orders/place", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["order"]["symbol"] == "GOOG"

def test_get_portfolio_summary():
    # Reuse acc_1 from previous test (mock state persists in memory)
    response = client.get("/portfolio/acc_1/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == "acc_1"
    assert data["portfolio_value"] > 0
