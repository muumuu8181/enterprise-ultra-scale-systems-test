import pytest
from src.models.monetization import PaymentSchedule

@pytest.mark.asyncio
async def test_get_earnings_dashboard(client):
    response = await client.get("/providers/prov_123/earnings-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "prov_123"
    assert data["total_revenue"] == 1000.0

@pytest.mark.asyncio
async def test_create_review(client):
    response = await client.post("/products/prod_1/reviews", json={
        "reviewer_id": "user_1",
        "rating": 5,
        "review_text": "Great API!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "prod_1"
    assert data["rating"] == 5
    assert data["review_text"] == "Great API!"

@pytest.mark.asyncio
async def test_get_reviews(client):
    # First create a review
    await client.post("/products/prod_1/reviews", json={
        "reviewer_id": "user_1",
        "rating": 5,
        "review_text": "Great API!"
    })

    response = await client.get("/products/prod_1/reviews")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["product_id"] == "prod_1"

@pytest.mark.asyncio
async def test_trending_apis(client):
    response = await client.get("/analytics/trending-apis")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "popularity_score" in data[0]
