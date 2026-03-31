import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Setup test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client():
    # create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_employee_and_get_score(client):
    from src.models.employee_models import Employee, EmployeeStatus
    async with TestingSessionLocal() as session:
        emp = Employee(employee_number="E001", name="Test User", department="Engineering", role="Dev", engagement_score=4.5, status=EmployeeStatus.ACTIVE)
        session.add(emp)
        await session.commit()
        await session.refresh(emp)
        emp_id = emp.id

    response = await client.get(f"/employees/{emp_id}/experience-score")
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == emp_id
    # (4.5 + 0)/2 because 0 surveys? Wait, logic says:
    # avg_sentiment = 0.0
    # if surveys: ...
    # return (employee.engagement_score + avg_sentiment) / 2
    # If no surveys, avg_sentiment is 0.0. So (4.5 + 0.0) / 2 = 2.25.
    assert data["experience_score"] == 2.25

@pytest.mark.asyncio
async def test_submit_survey(client):
    # Create employee first
    from src.models.employee_models import Employee, EmployeeStatus
    async with TestingSessionLocal() as session:
        emp = Employee(employee_number="E002", name="Survey User", department="Sales", role="Sales", engagement_score=3.0, status=EmployeeStatus.ACTIVE)
        session.add(emp)
        await session.commit()
        await session.refresh(emp)
        emp_id = emp.id

    payload = {
        "employee_id": emp_id,
        "survey_type": "pulse",
        "responses": {"q1": 5},
        "sentiment_score": 8.0, # Assuming 0-10 scale
        "anonymous": False
    }
    response = await client.post("/surveys/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == emp_id
    assert data["sentiment_score"] == 8.0

@pytest.mark.asyncio
async def test_get_survey_results(client):
    # Setup data
    from src.models.employee_models import Employee, SurveyResponse, SurveyType
    async with TestingSessionLocal() as session:
        emp = Employee(employee_number="E005", name="Result User", department="IT", role="Admin", engagement_score=4.0)
        session.add(emp)
        await session.flush()

        survey = SurveyResponse(
            employee_id=emp.id,
            survey_type=SurveyType.PULSE,
            responses={"q1": 4},
            sentiment_score=7.5,
            anonymous=True
        )
        session.add(survey)
        await session.commit()

    response = await client.get("/surveys/results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["sentiment_score"] == 7.5

@pytest.mark.asyncio
async def test_metrics(client):
    response = await client.get("/analytics/engagement-drivers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_attrition_risk(client):
    from src.models.employee_models import Employee, EmployeeStatus
    async with TestingSessionLocal() as session:
        # High risk employee
        emp = Employee(employee_number="E003", name="Risk User", department="HR", role="Recruiter", engagement_score=2.0, status=EmployeeStatus.ACTIVE)
        session.add(emp)
        await session.commit()

    response = await client.get("/analytics/attrition-risk")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["risk_level"] == "High"
