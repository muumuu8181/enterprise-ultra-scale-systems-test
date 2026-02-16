import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client():
    # Initialize tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # Cleanup (optional for in-memory, but good practice)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Music Streaming Platform API"}

@pytest.mark.asyncio
async def test_create_artist(client):
    response = await client.post(
        "/artists/",
        json={"name": "The Beatles", "bio": "Legendary band"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "The Beatles"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_artist(client):
    # create first
    response = await client.post(
        "/artists/",
        json={"name": "Test Artist", "bio": "Bio"},
    )
    artist_id = response.json()["id"]

    response = await client.get(f"/artists/{artist_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Artist"
    assert data["id"] == artist_id

@pytest.mark.asyncio
async def test_create_album(client):
    # Create artist first
    response = await client.post(
        "/artists/",
        json={"name": "Pink Floyd", "bio": "Prog Rock"},
    )
    artist_id = response.json()["id"]

    response = await client.post(
        "/albums/",
        json={"title": "The Dark Side of the Moon", "artist_id": artist_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Dark Side of the Moon"
    assert data["artist_id"] == artist_id
    assert "id" in data

@pytest.mark.asyncio
async def test_create_track(client):
    # Create artist
    r_artist = await client.post("/artists/", json={"name": "Artist X", "bio": "X"})
    artist_id = r_artist.json()["id"]

    # Create album
    r_album = await client.post("/albums/", json={"title": "Album Y", "artist_id": artist_id})
    album_id = r_album.json()["id"]

    # Create track
    response = await client.post(
        "/tracks/",
        json={
            "title": "Track Z",
            "duration": 200,
            "isrc": "US1234567890",
            "album_id": album_id
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Track Z"
    assert data["album_id"] == album_id
    assert "id" in data
