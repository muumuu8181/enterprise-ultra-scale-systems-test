import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from src.api.v1.rag import router, get_db
from src.models.rag_models import Document, DocumentChunk

# Setup App
app = FastAPI()
app.include_router(router)

# Mock DB Session
# We use a fixture to ensure a fresh mock for each test
@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session

@pytest.fixture
def client(mock_session):
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_pipeline():
    with patch("src.api.v1.rag.pipeline", new_callable=MagicMock) as mock:
        mock.ingest_document = AsyncMock()
        mock.retrieve = AsyncMock()
        mock.generate = AsyncMock()
        yield mock

def test_ingest_document(client, mock_pipeline, mock_session):
    # Setup Mock
    mock_doc = Document(
        id=1,
        title="Test Doc",
        chunk_count=2,
        ingested_at=datetime.now(timezone.utc),
        source_url="http://example.com"
    )
    mock_pipeline.ingest_document.return_value = mock_doc

    response = client.post(
        "/rag/documents/ingest",
        json={
            "title": "Test Doc",
            "text": "Hello World. This is a test.",
            "metadata": {"author": "Test"},
            "source_url": "http://example.com",
            "chunk_size": 100
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Doc"
    mock_pipeline.ingest_document.assert_called_once()

def test_query_rag(client, mock_pipeline, mock_session):
    # Setup Mock
    mock_chunks = [
        DocumentChunk(text="Chunk 1", embedding=[0.1]*1536),
        DocumentChunk(text="Chunk 2", embedding=[0.2]*1536)
    ]
    mock_pipeline.retrieve.return_value = mock_chunks
    mock_pipeline.generate.return_value = "This is the answer."

    response = client.post(
        "/rag/query",
        json={
            "question": "What is this?",
            "top_k": 2,
            "llm_model": "gpt-4"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is the answer."
    assert len(data["relevant_chunks"]) == 2
    assert data["relevant_chunks"][0] == "Chunk 1"
    mock_pipeline.retrieve.assert_called_once()
    mock_pipeline.generate.assert_called_once()

def test_get_document(client, mock_session):
    # Setup DB Mock for get
    mock_doc = Document(
        id=1,
        title="Test Doc",
        chunk_count=5,
        ingested_at=datetime.now(timezone.utc)
    )
    mock_session.get.return_value = mock_doc

    response = client.get("/rag/documents/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    mock_session.get.assert_called_with(Document, 1)

def test_get_document_not_found(client, mock_session):
    mock_session.get.return_value = None

    response = client.get("/rag/documents/999")

    assert response.status_code == 404

def test_delete_document(client, mock_session):
    mock_doc = Document(id=1)
    mock_session.get.return_value = mock_doc

    response = client.delete("/rag/documents/1")

    assert response.status_code == 204
    mock_session.delete.assert_called_once_with(mock_doc)
    mock_session.commit.assert_called_once()
