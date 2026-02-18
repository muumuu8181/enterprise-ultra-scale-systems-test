import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db
from src.models.learning_models import LearnerProfile, LearningPath, Assessment
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _get_db():
        yield mock_db_session
    return _get_db

@pytest.fixture
async def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_generate_learning_path(client, mock_db_session):
    # Mock finding learner
    mock_learner = LearnerProfile(id=1, user_id="user1")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_learner
    mock_db_session.execute.return_value = mock_result

    # Mock refresh to set ID on new path
    async def mock_refresh(obj):
        if isinstance(obj, LearningPath):
            obj.id = 101
    mock_db_session.refresh.side_effect = mock_refresh

    payload = {"learner_id": 1, "goal": "AI Mastery"}
    response = await client.post("/api/v1/learning/learning-paths/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 101
    assert data["goal"] == "AI Mastery"
    assert len(data["modules"]) > 0

@pytest.mark.asyncio
async def test_start_assessment(client, mock_db_session):
    # Mock finding assessment
    mock_assessment = Assessment(id=5, module_id="mod1")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_assessment
    mock_db_session.execute.return_value = mock_result

    payload = {"learner_id": 1}
    response = await client.post("/api/v1/learning/assessments/5/start", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "text" in data
    assert "options" in data

@pytest.mark.asyncio
async def test_submit_assessment(client, mock_db_session):
    # Mock finding learner for updating knowledge graph
    mock_learner = LearnerProfile(id=1, user_id="user1", knowledge_graph={"general": 0.5})

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_learner
    mock_db_session.execute.return_value = mock_result

    payload = {
        "learner_id": 1,
        "answers": {"q1": 1, "q2": 0}
    }

    response = await client.post("/api/v1/learning/assessments/5/submit", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] == True
    assert mock_db_session.commit.called
