import pytest
from httpx import AsyncClient, ASGITransport
from src.api.v1.risk import router
from src.db.session import get_db
from fastapi import FastAPI
from src.models.risk_models import Portfolio, PortfolioType

@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.mark.asyncio
async def test_api_endpoints(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create portfolio
        p = Portfolio(
            owner_id=1,
            portfolio_type=PortfolioType.EQUITY,
            total_value=100000.0,
            currency="USD"
        )
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)

        # Test VaR
        response = await ac.post(f"/portfolios/{p.id}/var-calculate", json={"confidence": 0.95, "horizon": 1})
        assert response.status_code == 200
        assert response.json()["var"] > 0

        # Test Stress
        response = await ac.post(f"/portfolios/{p.id}/stress-test", json={"scenario": {"market_shock": -0.10}})
        assert response.status_code == 200
        assert response.json()["loss_percentage"] == 10.0
