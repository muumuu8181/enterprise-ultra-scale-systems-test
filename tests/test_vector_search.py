from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.models.vector_models import VectorCollection

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AI/ML Integration Platform"}

def test_vector_router_registered():
    # FastAPI includes method in route, so we check path
    routes = [route.path for route in app.routes]
    assert "/vectors/collections" in routes
    assert "/vectors/index" in routes
    assert "/vectors/search" in routes

@patch("src.api.v1.vector_search.VectorStore")
def test_create_collection(MockVectorStore):
    # Setup mock
    mock_instance = MockVectorStore.return_value
    mock_instance.create_collection = AsyncMock(return_value=VectorCollection(
        id=1, name="test_col", dimension=128, metric="cosine", item_count=0, created_at="2024-01-01T00:00:00"
    ))

    response = client.post("/vectors/collections", json={"name": "test_col", "dimension": 128})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_col"
    assert data["dimension"] == 128
    assert data["metric"] == "cosine"

@patch("src.api.v1.vector_search.VectorStore")
def test_index_vector(MockVectorStore):
    mock_instance = MockVectorStore.return_value
    mock_instance.upsert_vector = AsyncMock()

    payload = {
        "collection": "test_col",
        "id": "vec1",
        "vector": [0.1] * 128,
        "metadata": {"key": "value"}
    }
    response = client.post("/vectors/index", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "id": "vec1"}

    mock_instance.upsert_vector.assert_called_once()

@patch("src.api.v1.vector_search.VectorStore")
def test_search_vectors(MockVectorStore):
    mock_instance = MockVectorStore.return_value
    # Mock return of search_nearest
    # It returns a list of VectorItem
    from src.models.vector_models import VectorItem
    mock_item = VectorItem(
        id=1, collection_id=1, external_id="vec1", metadata_={"key": "value"}
    )
    mock_instance.search_nearest = AsyncMock(return_value=[mock_item])

    payload = {
        "collection": "test_col",
        "query_vector": [0.1] * 128,
        "top_k": 5
    }
    response = client.post("/vectors/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["external_id"] == "vec1"
    assert data[0]["metadata"] == {"key": "value"}
