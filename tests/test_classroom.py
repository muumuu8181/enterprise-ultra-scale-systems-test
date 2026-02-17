import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from src.models.classroom_models import Base, VirtualClass, Enrollment, LiveSession, ClassStatus
from src.api.v1.classes import router, get_db

# Create a test app
app = FastAPI()
app.include_router(router)

# Test Database
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_class(client):
    response = await client.post("/classes/create", json={
        "instructor_id": "inst_1",
        "title": "Math 101",
        "subject": "Mathematics",
        "schedule": {"days": ["Mon", "Wed"], "time": "10:00"},
        "max_students": 30
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Math 101"
    assert "id" in data

@pytest.mark.asyncio
async def test_enroll_student(client):
    # First create class
    create_res = await client.post("/classes/create", json={
        "instructor_id": "inst_1",
        "title": "Math 101",
        "subject": "Mathematics",
        "schedule": {"days": ["Mon", "Wed"], "time": "10:00"},
        "max_students": 30
    })
    class_id = create_res.json()["id"]

    # Enroll
    response = await client.post(f"/classes/{class_id}/enroll", json={
        "student_id": "student_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["class_id"] == class_id
    assert data["student_id"] == "student_1"

@pytest.mark.asyncio
async def test_start_session(client):
    # Create class
    create_res = await client.post("/classes/create", json={
        "instructor_id": "inst_1",
        "title": "Math 101",
        "subject": "Mathematics",
        "schedule": {"days": ["Mon", "Wed"], "time": "10:00"},
        "max_students": 30
    })
    class_id = create_res.json()["id"]

    # Start session
    response = await client.post(f"/classes/{class_id}/start-session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "streaming_url" in data

    # Check live stream url endpoint
    url_res = await client.get(f"/classes/{class_id}/live-stream-url")
    assert url_res.status_code == 200
    assert "url" in url_res.json()
