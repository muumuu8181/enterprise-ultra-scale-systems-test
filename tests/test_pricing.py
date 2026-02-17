import pytest
from unittest.mock import patch
from src.models.pricing_models import Product, PricingRule, PriceChange, RuleType, PriceChangeReason

@pytest.mark.asyncio
async def test_reprice_flow(client, db_session):
    # Seed product
    product = Product(
        sku="P001",
        name="Test Product",
        category="Electronics",
        base_cost=100.0,
        current_price=150.0
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Test reprice
    payload = {
        "new_price": 145.0,
        "reason": "manual"
    }
    response = await client.post(f"/api/v1/products/{product.id}/reprice", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["new_price"] == 145.0

    # Verify history
    history = await client.get(f"/api/v1/products/{product.id}/price-history")
    assert history.status_code == 200
    history_data = history.json()
    assert len(history_data) == 1
    assert history_data[0]["new_price"] == 145.0
    assert history_data[0]["reason"] == "manual"

@pytest.mark.asyncio
async def test_create_rule(client, db_session):
    product = Product(
        sku="P002",
        name="Rule Product",
        category="Home",
        base_cost=50.0,
        current_price=80.0
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    payload = {
        "product_id": product.id,
        "rule_type": "markdown",
        "conditions": {"season": "winter"},
        "min_price": 40.0,
        "max_price": 100.0,
        "priority": 1
    }
    response = await client.post("/api/v1/rules/create", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["rule_type"] == "markdown"
    assert data["product_id"] == product.id

@pytest.mark.asyncio
async def test_optimization_endpoints(client):
    response = await client.get("/api/v1/optimization/recommendations?category=Electronics")
    assert response.status_code == 200
    assert "recommendations" in response.json()

    response = await client.post("/api/v1/optimization/simulate", json={"category": "Electronics", "strategy": "max_revenue"})
    assert response.status_code == 200
    assert "impact_forecast" in response.json()

@pytest.mark.asyncio
async def test_bulk_reprice(client):
    with patch("src.api.v1.pricing.optimize_price.delay") as mock_delay:
        mock_delay.return_value.id = "mock-task-id"
        response = await client.post("/api/v1/bulk-reprice", json={"product_ids": [1, 2, 3], "percentage_change": -0.1})
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        assert response.json()["job_id"] == "mock-task-id"
