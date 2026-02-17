import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.services import search_service

@pytest.mark.asyncio
async def test_create_workspace():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/workspaces/create", json={"name": "Test Workspace", "slug": "test-ws"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Workspace"

@pytest.mark.asyncio
async def test_search_service():
    results = await search_service.full_text_search(1, "test")
    assert len(results) == 2
    assert results[0].content == "Result for test 1"
