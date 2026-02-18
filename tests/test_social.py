import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database import Base, get_db
from src.main import app
from src.models.social_models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create test users
    db = TestingSessionLocal()
    user1 = User(id=1, username="user1", display_name="User One")
    user2 = User(id=2, username="user2", display_name="User Two")
    user3 = User(id=3, username="user3", display_name="User Three")
    db.add_all([user1, user2, user3])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_post(setup_db):
    response = client.post(
        "/api/v1/posts",
        json={"author_id": 1, "content": "Hello World", "media_urls": ["http://example.com/image.jpg"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello World"
    assert data["author_id"] == 1
    assert "id" in data

def test_get_post(setup_db):
    response = client.get("/api/v1/posts/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["content"] == "Hello World"

def test_like_post(setup_db):
    response = client.post("/api/v1/posts/1/like", json={"user_id": 2})
    assert response.status_code == 200
    assert response.json() == {"message": "Liked"}

    # Check like count
    response = client.get("/api/v1/posts/1")
    assert response.json()["likes_count"] == 1

def test_comment_post(setup_db):
    response = client.post(
        "/api/v1/posts/1/comments",
        json={"author_id": 3, "content": "Nice post!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Nice post!"
    assert data["post_id"] == 1

    # Check comments list
    response = client.get("/api/v1/posts/1/comments")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_delete_post(setup_db):
    response = client.delete("/api/v1/posts/1")
    assert response.status_code == 204

    response = client.get("/api/v1/posts/1")
    assert response.status_code == 404
