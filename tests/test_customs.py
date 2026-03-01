import pytest
import pytest_asyncio
import json
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.main import app
from src.database import get_db, Base
from src.models.customs_models import Declaration, TariffCode, Inspection, DeclarationType, InspectionType, DeclarationStatus, InspectionResult
import datetime

# Mock DB URL
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_submit_declaration():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/customs/declarations/submit", json={
            "reference_number": "REF123",
            "declaration_type": "import",
            "trader_id": "T001",
            "country_origin": "CN",
            "country_dest": "JP",
            "goods": [{"item": "Electronics", "quantity": 100}],
            "total_value": 50000.0,
            "currency": "USD"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["reference_number"] == "REF123"
    assert data["status"] == "submitted"

@pytest.mark.asyncio
async def test_lookup_tariff():
    # Insert dummy tariff
    async with TestingSessionLocal() as session:
        tariff = TariffCode(
            hs_code="8501.10",
            description="Electric motors",
            duty_rate_pct=5.0,
            vat_rate_pct=10.0,
            restrictions=[],
            preferential_agreements={},
            effective_date=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
        session.add(tariff)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/customs/tariffs/lookup", params={"hs_code": "8501.10"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["hs_code"] == "8501.10"

@pytest.mark.asyncio
async def test_calculate_duties():
    # Insert dummy tariff
    async with TestingSessionLocal() as session:
        tariff = TariffCode(
            hs_code="8501.10",
            description="Electric motors",
            duty_rate_pct=5.0,
            vat_rate_pct=10.0,
            restrictions=[],
            preferential_agreements={},
            effective_date=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
        session.add(tariff)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        goods_json = json.dumps([{"hs_code": "8501.10", "value": 1000.0}])
        response = await ac.get("/api/v1/customs/tariffs/calculate-duties", params={"goods": goods_json})

    assert response.status_code == 200
    data = response.json()
    # 5% of 1000 is 50
    assert data["total_duty"] == 50.0
    assert data["breakdown"]["8501.10"] == 50.0

@pytest.mark.asyncio
async def test_submit_inspection_result():
    # Insert declaration and inspection
    async with TestingSessionLocal() as session:
        decl = Declaration(
            reference_number="REF999",
            declaration_type=DeclarationType.IMPORT,
            trader_id="T002",
            country_origin="US",
            country_dest="JP",
            goods=[],
            total_value=1000.0,
            currency="USD",
            status=DeclarationStatus.SUBMITTED
        )
        session.add(decl)
        await session.commit()
        await session.refresh(decl)

        insp = Inspection(
            declaration_id=decl.id,
            inspection_type=InspectionType.PHYSICAL,
            result=InspectionResult.PENDING,
            scheduled_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
        session.add(insp)
        await session.commit()
        await session.refresh(insp)
        insp_id = insp.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/customs/inspections/{insp_id}/result", json={"result": "clear", "findings": "No issues"})

    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "clear"
    assert data["findings"] == "No issues"

    # Verify declaration status updated
    async with TestingSessionLocal() as session:
        result = await session.execute(
            Declaration.__table__.select().where(Declaration.id == decl.id)
        )
        updated_decl = result.mappings().one()
        assert updated_decl["status"] == "cleared"
