import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _get_db():
        yield mock_db_session
    return _get_db
